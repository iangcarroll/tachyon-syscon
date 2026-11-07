"""Pure input/oracle tests and actual original-vs-rebuilt physical executions."""
import copy
import hashlib
import json
import os
import tempfile
from pathlib import Path
import sys

import pytest

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / 'tools'))
from functional_scenarios import (InputError, compare_results, expected_outcome,
                                  load_scenario, mutate, replay, uart_ready, validate)


@pytest.fixture(scope='module')
def rebuilt_image(tmp_path_factory):
    from build_physical_firmware import build
    directory = tmp_path_factory.mktemp('functional-scenarios-build')
    manifest = build(directory)
    assert manifest['status'] == 'linked-experimental'
    assert manifest['inputs_unchanged_during_build']
    assert manifest['compile_failures'] == []
    assert manifest['unresolved_symbols'] == []
    assert manifest['layout_audit']['issues'] == []
    assert not manifest['endpoint_stubs_included']
    assert not manifest['original_executable_bytes_included']
    image = (directory / 'firmware.bin').read_bytes()
    assert hashlib.sha256(image).hexdigest() == manifest['binary_sha256']
    assert hashlib.sha256((directory / 'firmware.elf').read_bytes()).hexdigest() == manifest['elf_sha256']
    return image


def scenario_output(fallback, name, seed):
    configured = os.environ.get('SYSCON_SCENARIO_OUTPUT')
    if not configured:
        return fallback
    root = Path(configured).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    label = 'base' if seed is None else str(seed)
    return Path(tempfile.mkdtemp(prefix=f'{name}-seed-{label}-', dir=root))


def fixture(name='cold-command'):
    return json.loads((PACKAGE / 'fixtures/emulator/scenarios' / (name + '.json')).read_text())


@pytest.mark.parametrize('path,value', [
    (('version',), True), (('version',), 99), (('name',), '../escape'),
    (('startup',), 'patch-ram'), (('expect',), 'anything'),
    (('initial', 'adc_inputs', '9'), -1), (('initial', 'adc_inputs', '9'), 4096),
    (('initial', 'adc_inputs', '9'), True), (('initial', 'assumption'), ''),
    (('initial', 'gpio_inputs'), 1 << 32), (('initial', 'temperature_reference'), 0),
    (('rail_event', 'enabled'), 1), (('rail_event', 'after_key_ms'), -1),
    (('uart', 'ticks_per_byte'), 0), (('uart', 'policy'), 'implicit-mask-wait'), (('limits', 'tick_pumps'), 0),
    (('limits', 'instructions'), 1 << 32), (('limits', 'wall_seconds'), 0),
])
def test_invalid_input_fails_before_emulation(path, value):
    spec = fixture()
    node = spec
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    with pytest.raises(InputError):
        validate(spec)


@pytest.mark.parametrize('bad', [None, [], {}, {'version': 1}])
def test_bad_top_level(bad):
    with pytest.raises(InputError):
        validate(bad)


def test_unknown_fields_are_not_silently_ignored():
    spec = fixture()
    spec['rail_event']['after_key_mss'] = 1
    with pytest.raises(InputError):
        validate(spec)


def test_mutation_replays_and_does_not_mutate_base():
    spec = fixture()
    before = copy.deepcopy(spec)
    variants = [mutate(spec, seed) for seed in range(20)]
    assert spec == before
    assert variants[7] == mutate(spec, 7)
    assert len({json.dumps(item, sort_keys=True) for item in variants}) > 1
    assert all(validate(item) for item in variants)
    assert all(item['expect'] == spec['expect'] for item in variants)
    for invalid in [-1, True, 1 << 64]:
        with pytest.raises(InputError):
            mutate(spec, invalid)


def test_uart_readiness_requires_power_receiver_and_irq():
    base = 0x40100000
    registers = {base + 0x800: 1, base + 0x1100: 9, base + 0x1028: 1 << 10}
    assert uart_ready(registers, 1)
    for address in tuple(registers):
        disabled = dict(registers)
        disabled[address] = 0
        assert not uart_ready(disabled, 1)
    assert not uart_ready({}, 1)


def outcome(on):
    return {'termination': 'completed', 'initial_state': '0000',
            'key_events': ['release', 'assert', 'release'], 'state': '0202' if on else '0000',
            'mode': 2 if on else 1, 'rail_applied': on, 'uart_readiness_observed': on, 'uart_policy_satisfied': on,
            'uart1_reply_hex': b'Version=1.0.52\r\nPASS\r\n'.hex() if on else '',
            'persistence_verified': True, 'power_error_observed': not on, 'power_cut_observed': not on,
            'protocol_trace': [], 'persistence_trace': [], 'uart0_normalized_sha256': 'same',
            'final_expander': 'same', 'power_transitions': []}


def test_equal_but_stuck_off_does_not_pass():
    result = outcome(False)
    compared = compare_results(fixture(), [result, copy.deepcopy(result)])
    assert compared['equivalent'] and not compared['passed']


def test_negative_requires_error_power_cut_and_actual_key_sequence():
    spec = fixture('cold-no-rail')
    result = outcome(False)
    assert expected_outcome(spec, result)
    for field in ['power_error_observed', 'power_cut_observed']:
        broken = dict(result, **{field: False})
        assert not expected_outcome(spec, broken)
    for sequence in [[], ['release', 'assert'], ['release'], ['assert']]:
        assert not expected_outcome(spec, dict(result, key_events=sequence))
    assert not expected_outcome(spec, dict(result, termination='budget-exhausted'))


def test_readiness_protocol_and_persistence_mismatches_fail():
    spec = fixture('cold-autoboot')
    result = outcome(True)
    assert expected_outcome(spec, result)
    for changes in [{'uart_policy_satisfied': False}, {'persistence_verified': False},
                    {'uart1_reply_hex': b'ERSION\r\nFAIL\r\n'.hex()}]:
        assert not expected_outcome(spec, dict(result, **changes))
    for field in ['protocol_trace', 'persistence_trace']:
        other = dict(result, **{field: [{'payload': 'one byte changed'}]})
        assert not compare_results(spec, [result, other])['passed']


@pytest.mark.parametrize('name,seed', [('cold-command', None), ('cold-autoboot', None),
                                      ('cold-no-rail', None), ('cold-command', 73), ('cold-ready-paced', 73)])
def test_physical_cold_scenarios(tmp_path, rebuilt_image, name, seed):
    from inventory import load_image
    output = scenario_output(tmp_path, name, seed)
    result = replay(load_image(), rebuilt_image, fixture(name), output, seed)
    assert result['passed'], result
    assert result['expected_outcomes'] == [True, True]
    for role in ['original', 'rebuilt']:
        row = json.loads((output / (role + '-result.json')).read_text())
        assert row['termination'] == 'completed'
        assert row['minimum_msp'] >= 0x20000820
    if name == 'cold-autoboot':
        a = json.loads((output / 'original-result.json').read_text())
        b = json.loads((output / 'rebuilt-result.json').read_text())
        assert a['persistence_trace'] == b['persistence_trace']
        assert a['persistence_trace'][0]['flash_hex'] == a['persistence_trace'][1]['flash_hex']


def test_bounded_incomplete_run_never_passes(tmp_path):
    from inventory import load_image
    spec = fixture()
    spec['limits']['tick_pumps'] = 1
    result = replay(load_image(), load_image(), spec, tmp_path)
    assert not result['passed']
    assert set(result['termination'].values()) == {'budget-exhausted'}


def test_saved_replay_preserves_exact_mutation(tmp_path):
    spec = mutate(fixture(), 73)
    path = tmp_path / 'replay.json'
    path.write_text(json.dumps({'seed': 73, 'scenario': spec}))
    assert load_scenario(path) == spec
    assert load_scenario(path) != mutate(spec, 74)
    path.write_text(json.dumps({'seed': -1, 'scenario': spec}))
    with pytest.raises(InputError):
        load_scenario(path)
    path.write_text('{malformed')
    with pytest.raises(ValueError):
        load_scenario(path)


def test_interruption_does_not_leave_old_success(tmp_path, monkeypatch):
    import functional_scenarios as runner
    summary = tmp_path / 'summary.json'
    summary.write_text(json.dumps({'passed': True}))
    def interrupted(*args, **kwargs):
        raise RuntimeError('interrupted')
    monkeypatch.setattr(runner, 'execute', interrupted)
    with pytest.raises(RuntimeError, match='interrupted'):
        replay(b'original', b'candidate', fixture(), tmp_path)
    assert json.loads(summary.read_text()) == {'status': 'running', 'passed': False}


def test_temporary_irq_mask_waits_and_permanent_disable_is_bounded():
    from functional_scenarios import BudgetExceeded, wait_uart_ready
    base = 0x40100000
    registers = {base + 0x800: 1, base + 0x1100: 9, base + 0x1028: 0}
    advanced = []
    def step(count):
        advanced.append(count)
        if len(advanced) == 3:
            registers[base + 0x1028] = 1 << 10
    wait_uart_ready(lambda: registers, step, 1)
    assert len(advanced) == 3
    registers[base + 0x1028] = 0
    attempts = []
    with pytest.raises(BudgetExceeded, match='readiness'):
        wait_uart_ready(lambda: registers, attempts.append, 1, attempts=4)
    assert len(attempts) == 4


def test_uart_model_queues_masked_rx_and_pends_on_unmask():
    from inventory import load_image
    from mspm0.core import MCU
    machine = MCU(load_image())
    base = machine.device.BASES['UART1']
    machine.write_register(base + 0x800, 0x26000001)
    machine.write_register(base + 0x1100, 0x19)
    machine.write_register(base + 0x1028, 0)
    machine.device.inject_uart(1, b'V')
    assert bytes(machine.device.rx[1]) == b'V'
    assert not machine.irq_lines & (1 << 13)
    assert 29 not in machine.pending
    machine.write_register(base + 0x1028, 1 << 10)
    assert machine.irq_lines & (1 << 13)
    assert 29 in machine.pending
    assert machine.read_register(base + 0x1124) == ord('V')


def test_equal_final_state_with_different_power_action_order_is_rejected():
    spec = fixture()
    first = outcome(True)
    first['power_transitions'] = [
        {'domain': 'expander-0', 'mask': 4, 'enabled': 4, 'high': 4},
        {'domain': 'gpio-a', 'mask': 128, 'enabled': 128, 'high': 128},
    ]
    reordered = copy.deepcopy(first)
    reordered['power_transitions'].reverse()
    result = compare_results(spec, [first, reordered])
    assert result['expected_outcomes'] == [True, True]
    assert first['final_expander'] == reordered['final_expander']
    assert not result['passed']
    assert result['differing_fields'] == ['power_transitions']


def test_power_transition_decoder_preserves_direction_and_filters_noops():
    from functional_scenarios import PowerTransitions
    trace = PowerTransitions()
    off = trace.driven(0, 0, 255)
    hidden_latch = trace.driven(4, 0, 255)
    trace.change('expander-0', off, hidden_latch, 1)
    assert trace.events == []
    driven = trace.driven(4, 4, 255)
    trace.change('expander-0', hidden_latch, driven, 2)
    trace.change('expander-0', driven, driven, 3)
    low = trace.driven(0, 4, 255)
    trace.change('expander-0', driven, low, 4)
    trace.change('expander-0', low, off, 5)
    assert [event['enabled'] for event in trace.events] == [4, 4, 0]
    assert [event['high'] for event in trace.events] == [4, 0, 0]
    assert [event['ticks'] for event in trace.timed] == [2, 4, 5]


def test_boot_observer_installed_before_first_guest_instruction(tmp_path):
    from inventory import load_image
    from rebuilt_system import boot
    from functional_scenarios import PowerTransitions, scenario_input
    scenario = tmp_path / 'boot.json'
    scenario.write_text(json.dumps(scenario_input(fixture())))
    observed = []
    transitions = PowerTransitions()
    def attach(machine):
        observed.append(machine.instructions)
        transitions.attach(machine, 'test-reset')
    machine, _ = boot(load_image(), scenario, observer=attach)
    assert observed == [0]
    assert machine.boot_observation['main_loop_reached']
    assert transitions.events[0] == {'domain': 'reset', 'phase': 'test-reset'}
    assert any(event['domain'] == 'gpio-a' for event in transitions.events[1:])
    assert any(event['domain'].startswith('expander-') for event in transitions.events[1:])


@pytest.mark.parametrize('value', [None, ''])
def test_scenario_output_defaults_to_pytest_directory(tmp_path, monkeypatch, value):
    if value is None:
        monkeypatch.delenv('SYSCON_SCENARIO_OUTPUT', raising=False)
    else:
        monkeypatch.setenv('SYSCON_SCENARIO_OUTPUT', value)
    assert scenario_output(tmp_path, 'cold-command', None) == tmp_path


def test_scenario_output_preserves_unique_named_ci_runs(tmp_path, monkeypatch):
    root = tmp_path / 'ci' / 'scenarios'
    monkeypatch.setenv('SYSCON_SCENARIO_OUTPUT', str(root))
    first = scenario_output(tmp_path / 'fallback', 'cold-command', 73)
    second = scenario_output(tmp_path / 'fallback', 'cold-command', 73)
    baseline = scenario_output(tmp_path / 'fallback', 'cold-autoboot', None)
    assert first != second
    assert first.parent == second.parent == baseline.parent == root
    assert first.name.startswith('cold-command-seed-73-')
    assert baseline.name.startswith('cold-autoboot-seed-base-')
    marker = first / 'result.json'
    marker.write_text('preserved')
    assert second.is_dir() and marker.read_text() == 'preserved'
