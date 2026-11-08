"""Independent recovery rules and controls for the flash-prefix comparator."""
import copy
import random
from functools import reduce
from operator import xor

import pytest

from flash_interruptions import (CONFIG, IDENTITY, compare_captures, expected_after_boot,
                                fixture, lookup, slot, stack_log)


def test_fixture_encoding_covers_field_lengths_and_checksums():
    rng = random.Random(723)
    for length in range(1, 31):
        key = bytes(rng.choice(b'abcXYZ012_.-') for _ in range(length))
        value = bytes(rng.choice(b'abcXYZ012_.-') for _ in range(31 - length))
        encoded = slot(key, value)
        assert len(encoded) == 64
        assert lookup(encoded.ljust(1024, b'\xff'), key) == value
        for start in (0, 32):
            assert reduce(xor, encoded[start:start + 32], 0) == 0
            damaged = bytearray(encoded[start:start + 32])
            damaged[rng.randrange(32)] ^= 1 << rng.randrange(8)
            assert reduce(xor, damaged, 0) != 0


def test_recovery_model_preserves_legacy_invalid_slot_shadowing():
    key = b'boundary.key'
    initial = slot(b'confVersion', b'1') + slot(key, b'previous')
    pending = slot(key, b'replacement')[:32] + b'\xff' * 32
    page = (initial + pending).ljust(1024, b'\xff')
    assert lookup(page, key) == b'\xff' * 30
    assert expected_after_boot(page) == page
    damaged_version = bytearray(slot(b'confVersion', b'1'))
    damaged_version[31] ^= 1
    page = (damaged_version + slot(key, b'present')).ljust(1024, b'\xff')
    assert expected_after_boot(page) == page


def test_missing_version_reinitializes_the_entire_sector():
    for prefix in (b'', slot(b'other', b'value'), slot(b'confVersion', b'1')[:8]):
        page = prefix.ljust(1024, b'\xa5')
        restored = expected_after_boot(page)
        assert lookup(restored, b'confVersion') == b'1'
        assert lookup(restored, b'other') is None
        assert restored[64:] == b'\xff' * 960


def test_fixture_changes_only_persistent_input_regions():
    image = bytes(range(256)) * 256
    for case in ('append', 'compact'):
        prepared = fixture(image, case)
        assert prepared[:IDENTITY] == image[:IDENTITY]
        assert len(prepared) == len(image)
        assert lookup(prepared[CONFIG:], b'confVersion') == b'1'


@pytest.mark.parametrize('case', ['other', None])
def test_invalid_case_is_rejected(case):
    with pytest.raises(ValueError):
        fixture(b'', case)


def captured():
    first = b'\xff' * 65536
    after = bytearray(first)
    after[CONFIG:CONFIG + 8] = b'changed!'
    return dict(case='append', reply='reply', operations=[dict(kind='program', address=CONFIG, data='changed!')],
                controller=[('program', CONFIG, 'changed!', 3)],
                snapshots=[first, bytes(after)],
                unique=[dict(boundaries=[0]), dict(boundaries=[1])])


@pytest.mark.parametrize('mutation', ['operation', 'controller', 'early-flash', 'reply', 'groups', 'missing-boundary'])
def test_comparison_rejects_intermediate_differences(mutation):
    original = captured()
    candidate = copy.deepcopy(original)
    compare_captures(original, candidate)
    if mutation == 'operation':
        candidate['operations'][0]['address'] += 8
    elif mutation == 'controller':
        candidate['controller'][0] = ('program', CONFIG + 8, 'changed!', 3)
    elif mutation == 'early-flash':
        damaged = bytearray(candidate['snapshots'][0])
        damaged[CONFIG] ^= 1
        candidate['snapshots'][0] = bytes(damaged)
    elif mutation == 'reply':
        candidate['reply'] = 'other'
    elif mutation == 'groups':
        candidate['unique'][0]['boundaries'] = [1]
    else:
        candidate['snapshots'].pop(0)
    with pytest.raises(AssertionError):
        compare_captures(original, candidate)


def test_stack_diagnostic_can_vary_only_when_independently_correct():
    outputs = []
    for depth in (1008, 1016):
        text = f'[TIME] [CONF] Compaction: {depth} bytes of stack in use\r\n'.encode()
        outputs.append(stack_log(text, [dict(msp=0x20001000 - depth, reported=depth)]))
        with pytest.raises(AssertionError):
            stack_log(text, [dict(msp=0x20001000 - depth - 8, reported=depth)])
        with pytest.raises(AssertionError):
            stack_log(text, [])
    assert outputs[0] == outputs[1]


def test_stack_diagnostic_does_not_hide_unrelated_output():
    original = b'[TIME] [CONF] Compaction complete: 3 entries restored\r\n'
    changed = original.replace(b'3 entries', b'2 entries')
    assert stack_log(original, []) != stack_log(changed, [])
