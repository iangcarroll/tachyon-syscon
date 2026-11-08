"""Long button holds select boot modes through complete images and real GPIO IRQs."""
import json
import os
import re
import tempfile
import time
from pathlib import Path

import pytest

from build_physical_firmware import build
from functional_scenarios import PowerTransitions, scenario_input
from inventory import ROOT, load_image
from rebuilt_system import boot, command_reply, normalized_log

BUTTON = 1 << 12  # Tachyon button input, GPIOA12.
MODEM_KEY = 1 << 7  # Main processor's power-key output, GPIOA7.


@pytest.fixture(scope='module')
def physical(tmp_path_factory):
    output = tmp_path_factory.mktemp('button-physical')
    manifest = build(output)
    assert manifest['status'] == 'linked-experimental'
    assert manifest['inputs_unchanged_during_build']
    assert not manifest['layout_audit']['issues']
    return (output / 'firmware.bin').read_bytes(), manifest['layout_audit']['stack_floor_address']


def check_outcome(result, expected_mode):
    """Equality is insufficient: require the requested mode and completed output pulse."""
    assert result['modes'] == [expected_mode]
    assert result['rail_applied']
    assert result['task_completed']
    assert result['key_released_after_assert']
    assert result['version_responded']
    assert result['flash_unchanged']


def exercise(image, stack_floor, scenario, fastboot, edl_seconds, hold_ticks, output):
    power = PowerTransitions()
    started = time.monotonic()
    machine, _ = boot(image, scenario, observer=lambda m: power.attach(m, 0), stack_floor=stack_floor)
    key_asserted_at = None
    rail_applied = False
    commands = []

    def command(text):
        reply = command_reply(machine, text)
        assert b'[MFGD] PASS\r\n' in reply, reply
        commands.append(normalized_log(reply).hex())
        return reply

    # The periodic diagnostic reports compiler-dependent loop throughput.
    # Disable it through the public command, rather than deleting log lines.
    command('DIAG 0')
    command('CONFIG_SET sys.fastboot_enabled ' + ('true' if fastboot else 'false'))
    command('CONFIG_SET sys.edl_timer ' + str(edl_seconds))
    effective = command('CONFIG_INTERNAL')
    assert ('sys.edl_timer: ' + str(edl_seconds)).encode() in effective
    assert ('sys.fastboot_enabled: ' + ('true' if fastboot else 'false')).encode() in effective
    persisted = bytes(machine.flash)
    flash_events = len(machine.device.flash.events)
    before = len(machine.device.tx[0])
    power_before = len(power.events)
    assert not (machine.device.r.get(0x400a1280, 0) & machine.device.r.get(0x400a12c0, 0) & MODEM_KEY)

    def settle(ticks):
        nonlocal key_asserted_at, rail_applied
        for _ in range(ticks):
            assert time.monotonic() - started < 400, 'Button scenario exceeded wall-time budget'
            assert machine.instructions < 30_000_000, 'Button scenario exceeded instruction budget'
            assert machine.systick_ctrl & 3 == 3 and machine.systick_load, 'Button clock stopped'
            period = machine.systick_load + 1
            machine.advance(machine.systick_current + 1 if machine.systick_current else period)
            machine.run(2000)
            driven_key = machine.device.r.get(0x400a1280, 0) & machine.device.r.get(0x400a12c0, 0) & MODEM_KEY
            if driven_key and key_asserted_at is None:
                key_asserted_at = machine.cycles
            if key_asserted_at is not None and not rail_applied and machine.cycles - key_asserted_at >= 100 * period:
                # External synthetic processor rail responds to the observed key
                # output; neither image gets a private-state shortcut to ON.
                machine.device.adc_inputs[9] = 2048
                rail_applied = True

    try:
        settle(30)
        machine.device.set_gpio_inputs(0, BUTTON)
        settle(hold_ticks)
        machine.device.set_gpio_inputs(BUTTON, BUTTON)
        settle(3000)  # Includes release debounce, 2 s key pulse and trailing task actions.
        version = command('VERSION')
        log = bytes(machine.device.tx[0][before:])
        key_levels = [bool(event['high'] & MODEM_KEY) for event in power.events[power_before:]
                      if event['domain'] == 'gpio-a' and event['mask'] & MODEM_KEY
                      and event['enabled'] & MODEM_KEY]
        released = True in key_levels and False in key_levels[key_levels.index(True) + 1:]
        assert b'[DIAG]' not in log
        result = dict(commands=commands, uart=normalized_log(log).hex(), power=power.events,
                      modes=[mode.decode() for mode in re.findall(rb'\[560D\] setting mode to ([^\r]+)', log)],
                      rail_applied=rail_applied, task_completed=b'[STAT] Task completed\r\n' in log,
                      key_released_after_assert=released,
                      version_responded=b'Version=1.0.52\r\n' in version,
                      flash_unchanged=bytes(machine.flash) == persisted and len(machine.device.flash.events) == flash_events,
                      persistent=bytes(machine.flash[0xf800:]).hex())
        (output / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        return result
    finally:
        (output / 'uart.log').write_bytes(bytes(machine.device.tx[0]))
        (output / 'execution.json').write_text(json.dumps(dict(instructions=machine.instructions,
            wall_seconds=time.monotonic() - started, minimum_msp=machine.minimum_msp,
            stack_floor=stack_floor, power_transitions=power.timed), indent=2) + '\n')


@pytest.mark.parametrize('fastboot,edl_seconds,hold_ticks,expected_mode', [
    (False, 3, 3500, 'EDL'),
    (True, 3, 8500, 'FASTBOOT'),
    (True, 5, 8500, 'EDL'),
])
def test_complete_button_boot_sequence(physical, tmp_path, fastboot, edl_seconds, hold_ticks, expected_mode):
    if root := os.environ.get('SYSCON_SCENARIO_OUTPUT'):
        Path(root).mkdir(parents=True, exist_ok=True)
        tmp_path = Path(tempfile.mkdtemp(prefix='button-', dir=root))
    spec = json.loads((ROOT / 'tests/fixtures/emulator/scenarios/cold-command.json').read_text())
    spec['initial']['gpio_inputs'] |= BUTTON
    scenario = tmp_path / 'scenario.json'
    scenario.write_text(json.dumps(scenario_input(spec), indent=2) + '\n')
    (tmp_path / 'button.json').write_text(json.dumps(dict(fastboot=fastboot, edl_seconds=edl_seconds,
        hold_ticks=hold_ticks, expected_mode=expected_mode), indent=2) + '\n')
    results = []
    for role, image, floor in [('original', load_image(), 0x20000820), ('rebuilt', *physical)]:
        output = tmp_path / role
        output.mkdir()
        result = exercise(image, floor, scenario, fastboot, edl_seconds, hold_ticks, output)
        check_outcome(result, expected_mode)
        results.append(result)
    assert results[0] == results[1], 'UART, ordered power outputs or persistent bytes differ'


@pytest.mark.parametrize('field', ['rail_applied', 'task_completed', 'key_released_after_assert',
                                  'version_responded', 'flash_unchanged', 'modes'])
def test_matching_but_incomplete_or_wrong_boot_is_rejected(field):
    result = dict(modes=['FASTBOOT'], rail_applied=True, task_completed=True,
                  key_released_after_assert=True, version_responded=True, flash_unchanged=True)
    check_outcome(result, 'FASTBOOT')
    result[field] = ['EDL'] if field == 'modes' else False
    with pytest.raises(AssertionError):
        check_outcome(result, 'FASTBOOT')
