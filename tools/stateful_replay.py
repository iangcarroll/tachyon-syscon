"""Replay seeded external-input sessions against both complete firmware images.

No guest function is replaced and no private state is patched. The seed grammar
is deliberately bounded; saved event lists, rather than RNG implementation
details, are the replay contract. Virtual ticks are not physical MCU cycles.
"""
import argparse
import hashlib
import json
import random
import re
from pathlib import Path

from functional_scenarios import PowerTransitions
from inventory import load_image
from rebuilt_system import boot, candidate_stack_floor, normalized_log


def validate(events):
    if not isinstance(events, list) or not 1 <= len(events) <= 256:
        raise ValueError('Expected 1..256 events')
    for event in events:
        if not isinstance(event, dict) or 'kind' not in event:
            raise ValueError('Expected event object')
        kind = event['kind']
        fields = {
            'command': {'kind', 'text', 'spacing', 'status', 'contains'},
            'adc': {'kind', 'channel', 'sample'},
            'button': {'kind', 'hold_ticks'},
            'reset': {'kind'},
            'i2c-nack': {'kind', 'count'},
        }
        if not isinstance(kind, str) or kind not in fields or set(event) != fields[kind]:
            raise ValueError('Unknown event or fields')
        ranges = {'spacing': (5000, 12000), 'channel': (0, 31),
                  'sample': (0, 4095), 'hold_ticks': (90, 150), 'count': (1, 4)}
        for field, (low, high) in ranges.items():
            if field in event and (type(event[field]) is not int or not low <= event[field] <= high):
                raise ValueError('Invalid ' + field)
        if kind == 'command':
            for field in ('text', 'contains'):
                value = event[field]
                if not isinstance(value, str) or len(value) > 100 or any(not 32 <= ord(c) < 127 for c in value):
                    raise ValueError('Invalid command ' + field)
            if not event['text'] or event['status'] not in ('PASS', 'FAIL'):
                raise ValueError('Invalid command expectation')
    return events


def generate(seed, rounds=4):
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise ValueError('Seed must be an unsigned 64-bit integer')
    if type(rounds) is not int or not 2 <= rounds <= 12:
        raise ValueError('Rounds must be 2..12')
    rng = random.Random(seed)
    events = []

    def command(text, contains='', status='PASS'):
        events.append(dict(kind='command', text=text, spacing=rng.randint(5000, 12000),
                           status=status, contains=contains))

    command('VERSION', 'Version=1.0.52')
    values = {}
    button_after = rng.randrange(rounds)
    fault_after = rng.randrange(rounds)
    for index in range(rounds):
        key = 'replay.' + str(rng.randrange(2))
        value = ''.join(rng.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(rng.randint(1, 18)))
        values[key] = value
        command('CONFIG_SET ' + key + ' ' + value)
        command('CONFIG_GET ' + key, key + ' = ' + value)
        # Alternate rising/falling battery input; response direction is checked
        # independently of the original-vs-rebuilt comparison.
        sample = (1900 if index % 2 == 0 else 2900) + rng.randrange(100)
        events.append(dict(kind='adc', channel=2, sample=sample))
        command('READ_PWR', 'VBAT:')
        command(rng.choice(['VERSION', 'GPIO_READ 12', 'IOEXP_READ 0']))
        if rng.choice([False, True]):
            command('CONFIG_SET rejected %s', status='FAIL')
        if index == button_after:
            events.append(dict(kind='button', hold_ticks=rng.randint(90, 150)))
        if index == fault_after:
            events.append(dict(kind='i2c-nack', count=rng.randint(1, 3)))
            command('IOEXP_READ 0')
    events.append(dict(kind='reset'))
    for key, value in sorted(values.items()):
        command('CONFIG_GET ' + key, key + ' = ' + value)
    command('VERSION', 'Version=1.0.52')
    return validate(events)


def execute(image, events, stack_floor):
    validate(events)
    power = PowerTransitions()
    machine = None
    records = []
    assertions = []
    battery = []
    injected_nacks = 0
    observed_nacks = 0
    phase = 0

    def start(flash):
        return boot(flash, stack_floor=stack_floor,
                    observer=lambda m: power.attach(m, phase))[0]

    def settle(ticks):
        for _ in range(ticks):
            if machine.systick_ctrl & 3 != 3 or not machine.systick_load:
                raise AssertionError('Button clock stopped')
            machine.advance(machine.systick_load + 1)
            machine.run(2000)

    machine = start(image)
    initial_code = bytes(machine.flash[:0xf800])
    initial_identity = bytes(machine.flash[0xf800:0xfc00])
    for index, event in enumerate(events):
        before = len(machine.device.tx[0])
        flash_before = len(machine.device.flash.events)
        wire_before = len(machine.device.expander.events)
        power_before = len(power.events)
        kind = event['kind']
        if kind == 'command':
            for byte in event['text'].encode() + b'\n':
                machine.device.inject_uart(0, bytes([byte]))
                machine.run(event['spacing'])
            for _ in range(100):
                reply = bytes(machine.device.tx[0][before:])
                status = re.search(rb'(?m)^\[\d+\] \[MFGD\] (PASS|FAIL)\r$', reply)
                if status:
                    break
                machine.run(10000)
            else:
                raise AssertionError(f'Event {index}: UART response budget exhausted')
            assertions.append(status[1].decode() == event['status'] and event['contains'].encode() in reply)
            if event['text'] == 'READ_PWR':
                match = re.search(rb'\[MFGD\] VBAT: : (\d+)mV\r\n', reply)
                if not match:
                    raise AssertionError('Missing battery reading')
                battery.append((machine.device.adc_inputs[2], int(match[1])))
        elif kind == 'adc':
            machine.device.adc_inputs[event['channel']] = event['sample']
        elif kind == 'button':
            machine.device.set_gpio_inputs(1 << 12, 1 << 12)
            settle(30)
            machine.device.set_gpio_inputs(0, 1 << 12)
            settle(event['hold_ticks'])
            machine.device.set_gpio_inputs(1 << 12, 1 << 12)
            settle(300)
            reply = bytes(machine.device.tx[0][before:])
            assertions.append(all(token in reply for token in
                                  (b'Quick press seen', b'Quick press confirmed',
                                   b'PWR-KEY pressed', b'PWR-KEY released')))
        elif kind == 'i2c-nack':
            machine.device.expander.failures.extend(['nack'] * event['count'])
            injected_nacks += event['count']
        elif kind == 'reset':
            persisted = bytes(machine.flash)
            phase += 1
            machine = start(persisted)
            before = flash_before = wire_before = 0
            assertions.append(bytes(machine.flash) == persisted)
        if bytes(machine.flash[:0xf800]) != initial_code or bytes(machine.flash[0xf800:0xfc00]) != initial_identity:
            raise AssertionError('Session modified application or identity flash')
        nacks = sum(event[0] == 'wire-start' and event[-1] is True
                    for event in machine.device.expander.events[wire_before:])
        observed_nacks += nacks
        records.append(dict(event=index, i2c_nacks=nacks,
                            uart=normalized_log(bytes(machine.device.tx[0][before:])).hex(),
                            power=power.events[power_before:],
                            flash=[(kind, address, data.hex(), status) for kind, address, data, status
                                   in machine.device.flash.events[flash_before:]],
                            persistent=bytes(machine.flash[0xf800:]).hex()))
    return dict(records=records, assertions=assertions, battery=battery,
                power=power.events, injected_nacks=injected_nacks, observed_nacks=observed_nacks,
                pending_i2c_faults=len(machine.device.expander.failures))


def battery_responded(readings):
    if len(readings) < 2 or len({sample for sample, _ in readings}) < 2:
        return False
    return all((b[0] - a[0]) * (b[1] - a[1]) > 0 if a[0] != b[0] else a[1] == b[1]
               for a, b in zip(readings, readings[1:]))


def compare(results):
    expected = [bool(result['assertions']) and all(result['assertions']) and
                battery_responded(result['battery'])
                and any(event['domain'] != 'reset' for event in result['power'])
                and result['injected_nacks'] > 0 and result['observed_nacks'] == result['injected_nacks']
                and result['pending_i2c_faults'] == 0 for result in results]
    equal = len(results) == 2 and results[0] == results[1]
    return dict(passed=equal and all(expected), equivalent=equal, expected_outcomes=expected)


def replay(candidate, events, output):
    validate(events)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'events.json').write_text(json.dumps(events, indent=2) + '\n')
    summary_path = output / 'summary.json'
    summary_path.write_text(json.dumps(dict(passed=False, status='running')) + '\n')
    results = []
    try:
        images = [('original', load_image(), 0x20000820),
                  ('rebuilt', Path(candidate).read_bytes(), candidate_stack_floor(candidate))]
        for role, image, floor in images:
            result = execute(image, events, floor)
            (output / (role + '.json')).write_text(json.dumps(result, indent=2) + '\n')
            results.append(result)
        summary = compare(results)
        summary.update(status='completed', image_sha256={role: hashlib.sha256(image).hexdigest()
                                                       for role, image, _ in images})
    except Exception as error:
        summary = dict(passed=False, status='error', error=type(error).__name__ + ': ' + str(error))
    summary_path.write_text(json.dumps(summary, indent=2) + '\n')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--seed', type=int)
    source.add_argument('--events', type=Path)
    parser.add_argument('--rounds', type=int, default=4)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    events = generate(args.seed, args.rounds) if args.seed is not None else validate(json.loads(args.events.read_text()))
    summary = replay(args.candidate, events, args.output)
    print(json.dumps(summary, indent=2))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
