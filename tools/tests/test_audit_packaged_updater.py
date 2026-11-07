"""Offline updater audit. Set SYSCON_UPDATER_BINARY to the retained ELF copy.

No firmware/secret downloads or device discovery are performed by this fixture.
"""
import json
import os
from pathlib import Path
import pytest
import audit_packaged_updater as audit


@pytest.fixture(scope='module')
def binary_path():
    value = os.environ.get('SYSCON_UPDATER_BINARY')
    if not value:
        pytest.skip('set SYSCON_UPDATER_BINARY to a regular-file copy of the pinned ELF')
    path = Path(value)
    audit.read_pinned_binary(path)  # fail, never skip, for explicitly invalid input
    return path


@pytest.fixture(scope='module')
def blob(binary_path):
    return audit.read_pinned_binary(binary_path)


@pytest.mark.parametrize('length', audit.IMAGE_LENGTHS)
def test_actual_padding_and_packet_at_size_boundaries(blob, length):
    padded = audit.padded_length(blob, length)
    assert padded >= length and padded % 1024 == 0
    assert padded - length < 1024
    raw = audit.range_packet(blob, 0, padded)
    packet = audit.check_packet(raw, 0, padded)
    assert packet['inclusive_end'] + 1 == padded


@pytest.mark.parametrize('start,length', [(0,0), (0xffffffff,1), (0xffffffff,2), (0,0xffffffff)])
def test_actual_helper_modular_end_semantics(blob, start, length):
    raw = audit.range_packet(blob, start, length)
    result = audit.check_packet(raw, start, length)
    assert result['inclusive_end'] == (start + length - 1) & 0xffffffff


def test_first_byte_past_preservation_boundary_changes_erased_sector(blob):
    before = audit.padded_length(blob, 0xf800)
    after = audit.padded_length(blob, 0xf801)
    left = audit.check_packet(audit.range_packet(blob, 0, before), 0, before)
    right = audit.check_packet(audit.range_packet(blob, 0, after), 0, after)
    assert left['inclusive_end'] < 0xf800 <= right['inclusive_end']
    assert right['inclusive_end'] // 1024 > left['inclusive_end'] // 1024


@pytest.mark.parametrize('offset', [3, 4, 8, 12, 15])
def test_packet_negative_controls_reject_command_address_end_and_crc(blob, offset):
    packet = bytearray(audit.range_packet(blob, 0, 0xf800))
    packet[offset] ^= 1
    with pytest.raises(audit.AuditError, match='packet differs'):
        audit.check_packet(bytes(packet), 0, 0xf800)


def test_wrong_binary_fails_before_emulator(tmp_path, monkeypatch):
    path = tmp_path / 'changed.elf'
    path.write_bytes(b'not the packaged executable')
    def forbidden(*args):
        raise AssertionError('must not emulate an unpinned input')
    monkeypatch.setattr(audit, 'machine', forbidden)
    with pytest.raises(audit.AuditError, match='SHA256'):
        audit.audit(path)


def test_non_regular_binary_is_rejected(tmp_path):
    with pytest.raises(audit.AuditError, match='regular file'):
        audit.read_pinned_binary(tmp_path)


def test_failure_replaces_stale_success_report(tmp_path):
    output = tmp_path / 'report.json'
    output.write_text('{"passed":true}')
    assert audit.main(['--binary', str(tmp_path/'missing'), '--output', str(output)]) == 1
    assert json.loads(output.read_text())['passed'] is False


def test_cli_stdout_is_machine_readable(binary_path, capsys):
    assert audit.main(['--binary', str(binary_path)]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report['passed'] and report['hardware_access'] is False
    assert len(report['image_cases']) == len(audit.IMAGE_LENGTHS)
    assert any(c['reaches_config_at_0xf800'] for c in report['image_cases'])
    assert any(not c['reaches_config_at_0xf800'] for c in report['image_cases'])


def test_actual_instruction_negative_control_detects_end_off_by_one(blob, monkeypatch):
    original_machine = audit.machine
    def mutated_machine(data):
        cpu = original_machine(data)
        # Change SUB w2,w2,#1 to SUB w2,w2,#0 in the simulated image only.
        cpu.mem_write(0x26f8, bytes.fromhex('42000051'))
        return cpu
    monkeypatch.setattr(audit, 'machine', mutated_machine)
    raw = audit.range_packet(blob, 0, 0xf800)
    with pytest.raises(audit.AuditError, match='packet differs'):
        audit.check_packet(raw, 0, 0xf800)
