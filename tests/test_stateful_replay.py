"""Replay-contract tests; actual full-image sessions live in the integration suite."""
import copy
import json

import pytest

from stateful_replay import battery_responded, compare, generate, replay, validate


def test_seeded_sequences_are_reproducible_and_saved_events_are_the_contract(tmp_path):
    sequences = [generate(seed) for seed in range(20)]
    assert len({json.dumps(events) for events in sequences}) == len(sequences)
    # Inputs vary in placement as well as values: exercise commands/ADC both
    # before and after button handling and recoverable peripheral failures.
    placements = {(next(i for i, event in enumerate(events) if event['kind'] == 'button'),
                   next(i for i, event in enumerate(events) if event['kind'] == 'i2c-nack'))
                  for events in sequences}
    assert len(placements) > 1
    for seed, events in enumerate(sequences):
        assert events == generate(seed)
        path = tmp_path / 'events.json'
        path.write_text(json.dumps(events))
        assert validate(json.loads(path.read_text())) == events
        assert {'command', 'adc', 'reset', 'button', 'i2c-nack'} <= {event['kind'] for event in events}


@pytest.mark.parametrize('bad', [None, [], [None], [{'kind': []}], [{'kind': 'ram-patch'}],
                               [{'kind': 'reset', 'address': 0}],
                               [{'kind': 'button', 'hold_ticks': True}],
                               [{'kind': 'i2c-nack', 'count': 4}],
                               [{'kind': 'adc', 'channel': 2, 'sample': 4096}]])
def test_invalid_replay_is_rejected(bad):
    with pytest.raises(ValueError):
        validate(bad)


@pytest.mark.parametrize('field,value', [('text', 'VERSION\nREBOOT'), ('text', ''),
                                        ('contains', '\x00'), ('status', 'ANY'),
                                        ('spacing', 1), ('spacing', True)])
def test_command_contract_cannot_hide_missing_progress(field, value):
    events = generate(1)
    events[0][field] = value
    with pytest.raises(ValueError):
        validate(events)


def outcome():
    return dict(records=[{'uart': 'reply', 'flash': ['program'], 'power': ['edge']}],
                assertions=[True], battery=[(1900, 2505), (2950, 3889), (1950, 2570)],
                power=[{'domain': 'gpio-a'}], pending_i2c_faults=0,
                injected_nacks=2, observed_nacks=2)


def test_equal_but_stalled_sessions_are_rejected():
    for field, value in [('assertions', []), ('assertions', [False]),
                         ('battery', [(1900, 2505), (2950, 2505)]),
                         ('pending_i2c_faults', 1), ('observed_nacks', 0), ('power', [])]:
        result = dict(outcome(), **{field: value})
        checked = compare([result, copy.deepcopy(result)])
        assert checked['equivalent'] and not checked['passed']
    assert not compare([])['passed']
    assert not compare([outcome()])['passed']


@pytest.mark.parametrize('field', ['uart', 'flash', 'power'])
def test_intermediate_output_mutation_is_detected_even_with_matching_final_state(field):
    original = outcome()
    rebuilt = copy.deepcopy(original)
    assert compare([original, rebuilt])['passed']
    rebuilt['records'][0][field] = 'corrupted'
    assert not compare([original, rebuilt])['passed']


def test_battery_response_requires_rises_and_falls_to_follow_input():
    assert battery_responded(outcome()['battery'])
    assert not battery_responded([(1900, 2505), (2950, 2400)])
    assert not battery_responded([(1900, 2505)] * 3)
    assert not battery_responded([])


def test_recoverable_nack_range_matches_the_firmware_retry_boundary():
    for count in range(1, 4):
        event = {'kind': 'i2c-nack', 'count': count}
        assert validate([event]) == [event]
    for count in (0, 4, True):
        with pytest.raises(ValueError):
            validate([{'kind': 'i2c-nack', 'count': count}])


def test_missing_candidate_cannot_leave_a_stale_pass_or_running_result(tmp_path):
    (tmp_path / 'summary.json').write_text('{"passed":true}')
    result = replay(tmp_path / 'missing.bin', generate(1), tmp_path)
    assert result['status'] == 'error' and not result['passed']
    assert json.loads((tmp_path / 'summary.json').read_text()) == result
