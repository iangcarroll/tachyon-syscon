"""Physical-symbol proof, adversarial solver controls and independent ARM runs."""
import json
import random
import shutil
import struct
import subprocess

import pytest
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE, UC_HOOK_MEM_READ
from unicorn.arm_const import *

from inventory import load_image
from proof_checksum import compile_candidate, ProofError
import proof_physical_checksum
from proof_physical_checksum import compare, prove


REGISTERS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
             UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
             UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
             UC_ARM_REG_R12, UC_ARM_REG_SP, UC_ARM_REG_LR]


def execute(code, base, registers, nzcv, responses, fail_after=None):
    """Independent CPU check with an explicit response stream, not an MCU model.

    A first-failure prefix stops before the faulting load. This deliberately does
    not invent exception entry or equate different literal stacked fault PCs.
    """
    cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    cpu.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M0)
    pages = {base & ~4095, (base + len(code) - 1) & ~4095, (registers[14] & ~1) & ~4095}
    pages |= {((registers[0] + i) & 0xffffffff) & ~4095 for i in range(32)}
    for page in sorted(pages):
        cpu.mem_map(page, 4096)
    cpu.mem_write(base, code)
    for name, value in zip(REGISTERS, registers):
        cpu.reg_write(name, value)
    cpu.reg_write(UC_ARM_REG_XPSR, (1 << 24) | (nzcv << 28))
    states, reads = [], []
    stopped = False

    def before_instruction(uc, address, size, _):
        nonlocal stopped
        assert base <= address < base + len(code)
        states.append((address - base, tuple(uc.reg_read(r) for r in REGISTERS),
                       uc.reg_read(UC_ARM_REG_APSR) >> 28, len(reads)))
        opcode = struct.unpack_from('<H', code, address - base)[0]
        if fail_after is not None and len(reads) == fail_after and opcode & 0xf800 == 0x7800:
            stopped = True
            uc.emu_stop()

    def read(uc, kind, address, size, value, _):
        assert size == 1 and len(reads) < len(responses)
        byte = responses[len(reads)]
        # Prevent a test response from mutating immutable instruction bytes.
        assert not base <= address < base + len(code)
        uc.mem_write(address, bytes([byte]))
        reads.append((address, size, byte))

    cpu.hook_add(UC_HOOK_CODE, before_instruction)
    cpu.hook_add(UC_HOOK_MEM_READ, read)
    cpu.emu_start(base | 1, registers[14] & ~1, count=1000)
    assert stopped or cpu.reg_read(UC_ARM_REG_PC) == registers[14] & ~1
    return {'states': states, 'reads': reads, 'stopped': stopped,
            'registers': [cpu.reg_read(r) for r in REGISTERS],
            'nzcv': cpu.reg_read(UC_ARM_REG_APSR) >> 28}


@pytest.fixture(scope='module')
def physical_proof(tmp_path_factory):
    output = tmp_path_factory.mktemp('physical-checksum-proof')
    return output, prove(output)


def test_actual_physical_symbol_full_state_theorem_and_replay(physical_proof):
    output, report = physical_proof
    assert report['physical_symbol_bound'] and report['equivalent_under_read_event_contract']
    assert report['binaries_identical'] and report['status'] == 'unsat'
    assert not report['whole_firmware_equivalence']
    replay = subprocess.check_output(['z3', str(output / 'equivalence.smt2')], text=True)
    assert replay.strip() == 'unsat'
    obligations = json.loads((output / 'obligations.json').read_text())
    decisions = subprocess.check_output(['z3', str(output / 'obligations.smt2')], text=True).splitlines()
    assert decisions == [item['status'] for item in obligations]
    manifest = json.loads((output / 'physical-image/manifest.json').read_text())
    assert report['candidate_binary_sha256'] == manifest['binary_sha256']
    assert report['physical_build_inputs_sha256'] == manifest['build_input_sha256']


@pytest.mark.parametrize('pointer', [0, 0xffe0, 0x20000000, 0x20000fe1, 0x40080000, 0xfffffff0])
def test_physical_checksum_all_read_failure_prefixes_in_independent_cpu(physical_proof, pointer):
    _, report = physical_proof
    original = load_image()[0x282c:0x2840]
    candidate = bytes.fromhex(report['candidate_bytes'])
    rng = random.Random(pointer ^ 0x282c)
    for failure in [None, *range(report['reference_reads'])]:
        registers = [pointer] + [rng.getrandbits(32) for _ in range(14)]
        registers[13], registers[14] = 0x20000f00, 0x101
        flags = rng.randrange(16)
        responses = bytes(rng.randrange(256) for _ in range(report['reference_reads']))
        left = execute(original, 0x282c, registers, flags, responses, failure)
        right = execute(candidate, report['candidate_address'], registers, flags, responses, failure)
        assert left == right
        assert len(left['reads']) == (report['reference_reads'] if failure is None else failure)
        assert len(left['states']) <= report['instruction_boundaries_compared']


def test_changed_read_address_is_rejected_even_when_return_value_still_agrees(physical_proof, tmp_path):
    _, report = physical_proof
    mutant = bytearray.fromhex(report['candidate_bytes'])
    # Increase the LDRB offset by one. The common response stream still produces
    # the same checksum: only explicit address/state observations reject it.
    offset = next(i for i in range(0, len(mutant), 2)
                  if struct.unpack_from('<H', mutant, i)[0] & 0xf800 == 0x7800)
    opcode = struct.unpack_from('<H', mutant, offset)[0]
    struct.pack_into('<H', mutant, offset, opcode + (1 << 6))
    negative = compare(bytes(mutant), report['candidate_address'], tmp_path)
    assert negative['status'] == 'sat' and negative['return_value_difference_status'] == 'unsat'
    witness = negative['witness']
    args = (witness['initial_registers'], witness['initial_nzcv'], bytes.fromhex(witness['read_responses_hex']))
    left = execute(load_image()[0x282c:0x2840], 0x282c, *args)
    right = execute(bytes(mutant), report['candidate_address'], *args)
    assert left['registers'][0] == right['registers'][0]
    assert left['reads'] != right['reads']


def test_old_host_adapter_proof_does_not_establish_physical_full_register_abi(tmp_path):
    code, base, _, _, _, _ = compile_candidate(tmp_path / 'host-adapter')
    report = compare(code, base, tmp_path / 'comparison')
    assert report['status'] == 'sat' and report['return_value_difference_status'] == 'unsat'
    witness = report['witness']
    args = (witness['initial_registers'], witness['initial_nzcv'], bytes.fromhex(witness['read_responses_hex']))
    left = execute(load_image()[0x282c:0x2840], 0x282c, *args)
    right = execute(code, base, *args)
    assert left['registers'] == witness['reference_final_registers']
    assert right['registers'] == witness['candidate_final_registers']
    assert left['registers'][0] == right['registers'][0]
    assert left['registers'][1:4] != right['registers'][1:4]


def test_transient_register_difference_is_rejected_even_when_final_state_matches(physical_proof, tmp_path):
    _, proof = physical_proof
    original = bytes.fromhex(proof['candidate_bytes'])
    # Both MOVS copy R0, to distinct destinations. Swapping them preserves final
    # registers, flags and bus requests but changes the intermediate state.
    mutant = original[2:4] + original[:2] + original[4:]
    report = compare(mutant, proof['candidate_address'], tmp_path)
    assert report['status'] == 'sat' and report['return_value_difference_status'] == 'unsat'
    witness = report['witness']
    args = (witness['initial_registers'], witness['initial_nzcv'], bytes.fromhex(witness['read_responses_hex']))
    left = execute(original, 0x282c, *args)
    right = execute(mutant, proof['candidate_address'], *args)
    assert left['registers'] == right['registers']
    assert left['nzcv'] == right['nzcv'] and left['reads'] == right['reads']
    assert left['states'] != right['states']


@pytest.mark.parametrize('artifact', ['firmware.elf', 'firmware.bin', 'manifest.json'])
def test_artifact_replacement_during_proof_cannot_be_bound_to_success(physical_proof, tmp_path, monkeypatch, artifact):
    original_output, _ = physical_proof

    def existing_build(destination):
        destination.mkdir(parents=True)
        for name in ('firmware.elf', 'firmware.bin', 'manifest.json'):
            shutil.copyfile(original_output / 'physical-image' / name, destination / name)
        return json.loads((destination / 'manifest.json').read_text())

    real_compare = proof_physical_checksum.compare

    def racing_compare(code, base, output):
        report = real_compare(code, base, output)
        path = output / 'physical-image' / artifact
        changed = bytearray(path.read_bytes())
        changed[-1] ^= 1
        path.write_bytes(changed)
        return report

    monkeypatch.setattr(proof_physical_checksum, 'build', existing_build)
    monkeypatch.setattr(proof_physical_checksum, 'compare', racing_compare)
    with pytest.raises(ProofError, match='Physical artifact changed'):
        prove(tmp_path / 'race')
    report = json.loads((tmp_path / 'race/report.json').read_text())
    assert not report['physical_symbol_bound']


def test_failed_rebuild_does_not_leave_an_apparently_current_proof(tmp_path, monkeypatch):
    (tmp_path / 'report.json').write_text(json.dumps({'physical_symbol_bound': True, 'status': 'unsat'}))
    monkeypatch.setattr(proof_physical_checksum, 'build', lambda output: {'status': 'blocked'})
    with pytest.raises(ProofError, match='No successful stable physical source build'):
        prove(tmp_path)
    assert not (tmp_path / 'report.json').exists()
