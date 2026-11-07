"""Bounded whole-image cold-start scenarios; functional comparisons, no guest patches.

Imports the existing emulator modules beside this file once copied into tools/.
During prototype development put the repository tools/ directory on PYTHONPATH.
"""
import argparse
import copy
import hashlib
import json
import random
import re
import time
from pathlib import Path


class InputError(ValueError):
    pass


class BudgetExceeded(RuntimeError):
    pass


def _object(value, keys, where):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise InputError(f'{where}: expected fields {sorted(keys)}')


def _integer(value, low, high, where):
    if type(value) is not int or not low <= value <= high:
        raise InputError(f'{where}: expected integer {low}..{high}')


def validate(spec):
    _object(spec, ('version', 'name', 'initial', 'startup', 'rail_event', 'uart', 'limits', 'expect'), 'scenario')
    if spec['version'] != 1 or type(spec['version']) is not int:
        raise InputError('unsupported scenario version')
    if not isinstance(spec['name'], str) or not re.fullmatch(r'[a-z0-9-]{1,80}', spec['name']):
        raise InputError('name must be a short lowercase slug')
    if spec['startup'] not in ('command', 'persisted-auto'):
        raise InputError('startup must be command or persisted-auto')
    if spec['expect'] not in ('on', 'failed-power-on'):
        raise InputError('expect must be on or failed-power-on')
    initial = spec['initial']
    _object(initial, ('reset_cause', 'gpio_inputs', 'adc_inputs', 'temperature_reference', 'assumption'), 'initial')
    _integer(initial['reset_cause'], 0, 255, 'reset_cause')
    _integer(initial['gpio_inputs'], 0, 0xffffffff, 'gpio_inputs')
    _integer(initial['temperature_reference'], 1, 4095, 'temperature_reference')
    if not isinstance(initial['assumption'], str) or not initial['assumption'].strip():
        raise InputError('initial.assumption must describe constructed inputs')
    _object(initial['adc_inputs'], ('1', '2', '3', '5', '8', '9', '11'), 'adc_inputs')
    for channel, sample in initial['adc_inputs'].items():
        _integer(sample, 0, 4095, 'adc_inputs.' + channel)
    rail = spec['rail_event']
    _object(rail, ('enabled', 'after_key_ms', 'sample'), 'rail_event')
    if type(rail['enabled']) is not bool:
        raise InputError('rail_event.enabled must be boolean')
    _integer(rail['after_key_ms'], 0, 5000, 'after_key_ms')
    _integer(rail['sample'], 0, 4095, 'rail sample')
    _object(spec['uart'], ('policy', 'ready_settle_ms', 'ticks_per_byte'), 'uart')
    if spec['uart']['policy'] not in ('key-release-fixed', 'readiness-paced'):
        raise InputError('uart.policy must be key-release-fixed or readiness-paced')
    _integer(spec['uart']['ready_settle_ms'], 1, 100, 'ready_settle_ms')
    _integer(spec['uart']['ticks_per_byte'], 1000, 50000, 'ticks_per_byte')
    limits = spec['limits']
    _object(limits, ('tick_pumps', 'instructions_per_pump', 'instructions', 'wall_seconds'), 'limits')
    for key, low, high in [('tick_pumps', 1, 10000), ('instructions_per_pump', 100, 20000),
                           ('instructions', 1000, 50000000), ('wall_seconds', 1, 600)]:
        _integer(limits[key], low, high, 'limits.' + key)
    return spec


def load_scenario(path):
    """Accept a seed fixture or an exact saved replay; never reapply its seed."""
    value = json.loads(Path(path).read_text())
    if isinstance(value, dict) and set(value) == {'seed', 'scenario'}:
        if value['seed'] is not None:
            _integer(value['seed'], 0, (1 << 64) - 1, 'recorded seed')
        value = value['scenario']
    return validate(value)


def mutate(spec, seed):
    """Small replayable mutations that retain the seed scenario's intended domain."""
    validate(spec)
    _integer(seed, 0, (1 << 64) - 1, 'seed')
    changed = copy.deepcopy(spec)
    rng = random.Random(seed)
    changed['rail_event']['after_key_ms'] = rng.randrange(50, 251)
    changed['uart']['ticks_per_byte'] = rng.randrange(5000, 12001)
    changed['initial']['adc_inputs']['1'] = rng.randrange(1423, 1434)
    return validate(changed)


def scenario_input(spec):
    initial = spec['initial']
    factory = bytearray(128)
    factory[0x3c:0x40] = initial['temperature_reference'].to_bytes(4, 'little')
    return {'name': spec['name'], 'hardware_capture': False, 'nonmain_fill': 0,
            'factory_hex': factory.hex(), 'reset_cause': initial['reset_cause'],
            'gpio_inputs': initial['gpio_inputs'], 'adc_inputs': initial['adc_inputs'],
            'writeonly_read_fixtures': {'0x400a1048': 0},
            'description': initial['assumption']}


def uart_ready(registers, port):
    base = (0x40108000, 0x40100000)[port]
    return bool(registers.get(base + 0x800, 0) & 1 and
                registers.get(base + 0x1100, 0) & 9 == 9 and
                registers.get(base + 0x1028, 0) & (1 << 10))


def wait_uart_ready(registers, advance, port, attempts=100):
    """A transient RX IRQ mask is a critical section, not a failed UART."""
    for _ in range(attempts):
        if uart_ready(registers(), port):
            return
        advance(100)
    raise BudgetExceeded('UART readiness wait limit')


class PowerTransitions:
    """Observe effective digital outputs, retaining global GPIO/I2C order.

    GPIO values are sampled after the MCU's MMIO hook. Accepted expander frames
    are decoded byte by byte so a multibyte transfer cannot hide intermediate
    direction/output changes. Pointer-only polling reads and no-op writes do
    not create transitions. Nothing is written back to the guest or model.
    """
    def __init__(self):
        self.events = []
        self.timed = []

    @staticmethod
    def driven(latch, enabled, mask):
        return (latch & enabled & mask, enabled & mask)

    def change(self, domain, before, after, ticks):
        high_before, enabled_before = before
        high_after, enabled_after = after
        changed = (enabled_before ^ enabled_after) | (high_before ^ high_after)
        if changed:
            event = {'domain': domain, 'mask': changed,
                     'enabled': enabled_after & changed, 'high': high_after & changed}
            self.events.append(event)
            self.timed.append(dict(event, ticks=ticks))

    def attach(self, machine, phase):
        from unicorn import UC_HOOK_MEM_WRITE
        self.events.append({'domain': 'reset', 'phase': phase})
        self.timed.append({'domain': 'reset', 'phase': phase, 'ticks': machine.cycles})
        device = machine.device
        gpio = self.driven(device.r.get(0x400a1280, 0), device.r.get(0x400a12c0, 0), 0xffffffff)
        expander = bytearray(device.expander.expander)
        event_index = len(device.expander.events)

        def observe(cpu, kind, address, size, value, unused):
            nonlocal gpio, event_index
            next_gpio = self.driven(device.r.get(0x400a1280, 0), device.r.get(0x400a12c0, 0), 0xffffffff)
            self.change('gpio-a', gpio, next_gpio, machine.cycles)
            gpio = next_gpio
            pending = device.expander.events[event_index:]
            event_index = len(device.expander.events)
            for event in pending:
                if event[0] != 'wire-write' or event[1] != 0x26 or len(event[2]) < 2:
                    continue
                frame = event[2]
                register = frame[0] & 7
                for byte in frame[1:]:
                    bank = register & 1
                    before = self.driven(expander[bank + 2], ~expander[bank + 6], 255)
                    if register >= 2:
                        if register in (2, 3):
                            byte &= ~(device.expander.stuck_low >> (8 * (register - 2))) & 255
                        expander[register] = byte
                    after = self.driven(expander[bank + 2], ~expander[bank + 6], 255)
                    self.change('expander-' + str(bank), before, after, machine.cycles)
                    register = (register & 6) | ((register + 1) & 1)
            # A decoder mismatch is a harness failure, not silently normalized.
            if expander[2:] != device.expander.expander[2:]:
                raise AssertionError('Expander output observer disagrees with peripheral state')

        return machine.cpu.hook_add(UC_HOOK_MEM_WRITE, observe, begin=0x40000000, end=0xffffffff)


def expected_outcome(spec, result):
    """Independent positive/negative oracle: equality alone never implies success."""
    if result['termination'] != 'completed':
        return False
    events = result['key_events']
    try:
        assertion = events.index('assert')
        released = 'release' in events[assertion + 1:]
    except ValueError:
        released = False
    if not released or result['initial_state'] != '0000':
        return False
    if spec['startup'] == 'persisted-auto' and not result['persistence_verified']:
        return False
    if spec['expect'] == 'on':
        return (result['state'] == '0202' and result['mode'] == 2 and result['rail_applied'] and
                result['uart_policy_satisfied'] and
                result['uart1_reply_hex'] == b'Version=1.0.52\r\nPASS\r\n'.hex())
    return (result['state'] == '0000' and result['mode'] == 1 and
            result['power_error_observed'] and result['power_cut_observed'] and
            result['uart1_reply_hex'] == '' and not result['rail_applied'])


def compare_results(spec, results):
    """External behavior/state relation, deliberately excluding scratch registers."""
    expected = [expected_outcome(spec, result) for result in results]
    fields = ('state', 'mode', 'key_events', 'uart1_reply_hex', 'protocol_trace',
              'persistence_trace', 'uart0_normalized_sha256', 'final_expander', 'power_transitions')
    equivalent = len(results) == 2 and all(results[0][field] == results[1][field] for field in fields)
    return {'expected_outcomes': expected, 'equivalent': equivalent,
            'passed': len(results) == 2 and all(expected) and equivalent,
            'differing_fields': [field for field in fields if len(results) == 2 and results[0][field] != results[1][field]]}


def execute(image, spec, output, role):
    """Execute real reset/IRQ/main code; all writes are external peripheral stimuli."""
    from rebuilt_system import boot, normalized_log
    from unicorn import UC_HOOK_MEM_WRITE
    validate(spec)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    scenario_path = output / 'input.json'
    scenario_path.write_text(json.dumps(scenario_input(spec), indent=2) + '\n')
    started = time.monotonic()
    total_instructions = 0
    machine = None
    trace = []
    power = PowerTransitions()
    reset_index = 0
    protocol = []
    persistence = []
    key_events = []
    key_tick = None
    released = False
    raised = False
    ready_seen = False
    policy_satisfied = False
    ready_since = None
    reply = b''
    initial_state = None
    persistence_verified = spec['startup'] != 'persisted-auto'
    limits = spec['limits']
    result = {'role': role, 'image_sha256': hashlib.sha256(image).hexdigest(),
              'termination': 'completed', 'error': None}

    def check_budget():
        if time.monotonic() - started > limits['wall_seconds']:
            raise BudgetExceeded('wall-time limit')
        if total_instructions + (machine.instructions if machine else 0) >= limits['instructions']:
            raise BudgetExceeded('instruction limit')

    def external_events():
        nonlocal raised
        rail = spec['rail_event']
        period = machine.systick_load + 1
        if rail['enabled'] and key_tick is not None and not raised and machine.cycles - key_tick >= rail['after_key_ms'] * period:
            machine.device.adc_inputs[9] = rail['sample']
            raised = True
            trace.append({'event': 'external-rail', 'ticks': machine.cycles, 'sample': rail['sample']})

    def run(count):
        check_budget()
        remaining = limits['instructions'] - total_instructions - machine.instructions
        machine.run(min(count, remaining))
        external_events()
        check_budget()

    def pace(ticks):
        deadline = machine.cycles + ticks
        while machine.cycles < deadline:
            previous = machine.cycles
            run(min(2000, deadline - machine.cycles))
            if machine.cycles == previous:
                machine.advance(deadline - machine.cycles)
                external_events()
        check_budget()

    def command(text):
        before = len(machine.device.tx[0])
        for value in text.encode() + b'\n':
            machine.device.inject_uart(0, bytes([value]))
            pace(spec['uart']['ticks_per_byte'])
        for _ in range(200):
            data = bytes(machine.device.tx[0][before:])
            status = re.search(rb'(?m)^\[\d+\] \[MFGD\] (PASS|FAIL)\r$', data)
            if status:
                # Protocol records retain exact payload bytes and normalized framing.
                protocol.append({'command': text, 'response_hex': normalized_log(data).hex()})
                if status[1] != b'PASS':
                    raise AssertionError('command rejected: ' + text)
                return data
            run(10000)
        raise BudgetExceeded('command response budget')

    def cold_start(flash):
        nonlocal machine, reset_index
        check_budget()
        phase = 'configuration-setup' if spec['startup'] == 'persisted-auto' and reset_index == 0 else 'scenario'
        machine, _ = boot(flash, scenario_path,
                          budget=min(2000000, limits['instructions'] - total_instructions),
                          observer=lambda initialized: power.attach(initialized, phase))
        reset_index += 1
        check_budget()

    try:
        cold_start(image)
        if spec['startup'] == 'persisted-auto':
            command('CONFIG_SET sys.auto_boot true')
            readback = command('CONFIG_GET sys.auto_boot')
            if b'sys.auto_boot = true' not in readback:
                raise AssertionError('configuration readback absent')
            configured = bytes(machine.flash)
            persistence.append({'phase': 'configured', 'flash_hex': configured[0xf800:].hex()})
            total_instructions += machine.instructions
            machine = None
            cold_start(configured)
            persistence.append({'phase': 'fresh-reset', 'flash_hex': bytes(machine.flash[0xf800:]).hex()})
            persistence_verified = persistence[-1]['flash_hex'] == persistence[-2]['flash_hex']
        initial_state = bytes(machine.cpu.mem_read(0x200004f1, 2)).hex()

        def observe(cpu, kind, address, size, value, unused):
            nonlocal key_tick, released
            if size != 4 or not value & 128:
                return
            if address == 0x400a1290:
                key_tick = machine.cycles
                released = False
                key_events.append('assert')
                trace.append({'event': 'key-assert', 'ticks': machine.cycles})
            elif address == 0x400a12a0:
                if key_tick is not None:
                    released = True
                key_events.append('release')
                trace.append({'event': 'key-release', 'ticks': machine.cycles})

        machine.cpu.hook_add(UC_HOOK_MEM_WRITE, observe)
        if spec['startup'] == 'command':
            command('POWER:NORMAL:;')
        for _ in range(limits['tick_pumps']):
            check_budget()
            period = machine.systick_load + 1
            machine.advance(machine.systick_current + 1 if machine.systick_current else period)
            run(limits['instructions_per_pump'])
            fixed = spec['uart']['policy'] == 'key-release-fixed'
            if released and (fixed or uart_ready(machine.device.r, 1)):
                if ready_since is None:
                    ready_since = machine.cycles
                if machine.cycles - ready_since >= spec['uart']['ready_settle_ms'] * period:
                    policy_satisfied = True
                    ready_seen = uart_ready(machine.device.r, 1)
            else:
                ready_since = None
            state = bytes(machine.cpu.mem_read(0x200004f1, 2)).hex()
            log = bytes(machine.device.tx[0])
            if spec['expect'] == 'on' and policy_satisfied:
                break
            if spec['expect'] == 'failed-power-on' and state == '0000' and released and b'Modem power ERROR: power on never completed' in log and b'auto-boot pending' in log:
                break
        else:
            raise BudgetExceeded('event/tick-pump limit')
        if spec['expect'] == 'on':
            before = len(machine.device.tx[1])
            for value in b'VERSION\n':
                if spec['uart']['policy'] == 'readiness-paced':
                    wait_uart_ready(lambda: machine.device.r, run, 1)
                trace.append({'event': 'uart1-rx', 'ticks': machine.cycles, 'byte': value})
                machine.device.inject_uart(1, bytes([value]))
                pace(spec['uart']['ticks_per_byte'])
            for _ in range(100):
                reply = bytes(machine.device.tx[1][before:])
                if b'PASS\r\n' in reply or b'FAIL\r\n' in reply:
                    break
                run(20000)
            else:
                raise BudgetExceeded('UART1 response limit')
    except BudgetExceeded as error:
        result.update(termination='budget-exhausted', error=str(error))
    except Exception as error:
        result.update(termination='fault', error=type(error).__name__ + ': ' + str(error))
    if machine:
        persistence.append({'phase': 'session-end', 'flash_hex': bytes(machine.flash[0xf800:]).hex()})
    log = bytes(machine.device.tx[0]) if machine else b''
    result.update(initial_state=initial_state,
        state=bytes(machine.cpu.mem_read(0x200004f1, 2)).hex() if machine else None,
        mode=int.from_bytes(machine.cpu.mem_read(0x20000450, 1), 'little') if machine else None,
        key_events=key_events, rail_applied=raised, uart_readiness_observed=ready_seen,
        uart_policy=spec['uart']['policy'], uart_policy_satisfied=policy_satisfied,
        uart1_reply_hex=reply.hex(), protocol_trace=protocol, persistence_trace=persistence,
        persistence_verified=persistence_verified, power_error_observed=b'Modem power ERROR: power on never completed' in log,
        power_cut_observed=b'powering down by cutting power' in log,
        uart0_normalized_sha256=hashlib.sha256(normalized_log(log)).hexdigest(),
        final_expander=machine.device.expander.expander.hex() if machine else None,
        power_transitions=power.events,
        minimum_msp=machine.minimum_msp if machine else None,
        instructions=total_instructions + (machine.instructions if machine else 0),
        wall_seconds=time.monotonic() - started)
    (output / (role + '-trace.json')).write_text(json.dumps({'events': trace, 'power_transitions_timed': power.timed, 'uart0_hex': log.hex(),
        'model_events': [repr(event) for event in machine.events] if machine else []}, indent=2) + '\n')
    result['expected_outcome_passed'] = expected_outcome(spec, result)
    (output / (role + '-result.json')).write_text(json.dumps(result, indent=2) + '\n')
    return result


def replay(original, candidate, spec, output, seed=None):
    """All bulky traces go to output; returned summary is intentionally small."""
    validate(spec)
    if seed is not None:
        spec = mutate(spec, seed)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'summary.json').write_text(json.dumps({'status': 'running', 'passed': False}) + '\n')
    (output / 'replay.json').write_text(json.dumps({'seed': seed, 'scenario': spec}, indent=2) + '\n')
    results = [execute(image, spec, output, role) for role, image in [('original', original), ('rebuilt', candidate)]]
    summary = compare_results(spec, results)
    summary.update(status='completed', name=spec['name'], seed=seed, output=str(output),
                   image_sha256={result['role']: result['image_sha256'] for result in results},
                   termination={result['role']: result['termination'] for result in results},
                   hardware_capture=False, physical_cycle_accuracy=False, firmware_function_replacements=[],
                   uart_policy=spec['uart']['policy'], uart_ticks_per_byte=spec['uart']['ticks_per_byte'])
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('scenario', type=Path)
    parser.add_argument('--original', required=True, type=Path)
    parser.add_argument('--candidate', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--seed', type=int)
    args = parser.parse_args()
    try:
        spec = load_scenario(args.scenario)
        summary = replay(args.original.read_bytes(), args.candidate.read_bytes(), spec, args.output, args.seed)
    except (InputError, ValueError, OSError) as error:
        parser.error(str(error))
    print(json.dumps(summary, indent=2))
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
