"""Prove the linked checksum's complete register/read-event relation.

This is a function theorem, not whole-image equivalence. The environment must
supply equal responses to equal ordered byte reads. Read addresses may be any
32-bit value, including wrapping, inaccessible or changing device addresses.
Equal pre-read states establish the relation at every possible first read
failure; exception entry, literal fault PCs and interrupt handlers are outside
this theorem. PC is related by function-relative offset until BX LR.
"""
import argparse
import hashlib
import io
import json
import subprocess
from pathlib import Path

from elftools.elf.elffile import ELFFile

from build_physical_firmware import build
from inventory import ROOT, EXPECTED, load_image
from proof_checksum import Problem, ProofError, Thumb, eq, number, sexpr


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def extract_function(path, name):
    # Parse the same immutable bytes that the caller hashed, not a second open
    # of a potentially replaced build artifact.
    data = path if isinstance(path, bytes) else Path(path).read_bytes()
    with io.BytesIO(data) as stream:
        elf = ELFFile(stream)
        if elf.elfclass != 32 or elf['e_machine'] != 'EM_ARM':
            raise ProofError('Candidate is not an ARM ELF32 image')
        symbols = elf.get_section_by_name('.symtab').get_symbol_by_name(name)
        if not symbols or len(symbols) != 1:
            raise ProofError('Expected one defined checksum function')
        symbol = symbols[0]
        if symbol['st_info']['type'] != 'STT_FUNC' or not isinstance(symbol['st_shndx'], int):
            raise ProofError('Checksum symbol is not a defined function')
        section = elf.get_section(symbol['st_shndx'])
        base, size = symbol['st_value'] & ~1, symbol['st_size']
        offset = base - section['sh_addr']
        if not section['sh_flags'] & 4 or size < 2 or offset < 0 or offset + size > section['sh_size']:
            raise ProofError('Checksum is outside an executable section')
        return section.data()[offset:offset + size], base


def _different(left, right):
    if len(left) != len(right):
        return ['true']
    return [f'(not {eq(a,b)})' for a, b in zip(left, right)]


def compare(code, base, output):
    """Symbolically compare supplied candidate instructions; no build claim."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    for name in ('report.json', 'equivalence.smt2', 'obligations.smt2', 'obligations.json', 'counterexample.smt2'):
        (output / name).unlink(missing_ok=True)
    proof_inputs = {str(path.relative_to(ROOT)): digest(path) for path in (
        Path(__file__), ROOT / 'tools/proof_checksum.py', ROOT / 'tools/inventory.py')}
    original = load_image()[0x282c:0x2840]
    problem = Problem(read_events=True)
    if problem.query('true')[0] != 'sat':
        raise ProofError('Input contract is inconsistent')
    reference = Thumb(problem, original, 0x282c, trace_states=True).run()
    candidate = Thumb(problem, code, base, trace_states=True).run()

    differences = _different(reference.r, candidate.r)
    differences += _different(tuple(reference.f.values()), tuple(candidate.f.values()))
    differences += _different([reference.return_target], [candidate.return_target])
    if len(reference.reads) != len(candidate.reads):
        differences.append('true')
    else:
        for left, right in zip(reference.reads, candidate.reads):
            differences += _different(left, right)
    if len(reference.states) != len(candidate.states):
        differences.append('true')
    else:
        for left, right in zip(reference.states, candidate.states):
            if (left['offset'], left['reads_completed']) != (right['offset'], right['reads_completed']):
                differences.append('true')
            differences += _different(left['registers'], right['registers'])
            differences += _different(left['flags'], right['flags'])
    mismatch = '(or ' + ' '.join(differences) + ')'
    status, _ = problem.query(mismatch)
    (output / 'equivalence.smt2').write_text(problem.script(mismatch))
    return_status, _ = problem.query(f'(not {eq(reference.r[0],candidate.r[0])})')

    witness = None
    if status == 'sat':
        inputs = ['pointer'] + [f'initial_r{i}' for i in range(1, 15)]
        flags = ['initial_' + name for name in 'NZCV']
        responses = [f'input_read_byte{i}' for i in range(max(len(reference.reads), len(candidate.reads)))]
        left = [problem.bind(value) for value in reference.r]
        right = [problem.bind(value) for value in candidate.r]
        names = inputs + flags + responses + left + right
        witness_status, answer = problem.query(mismatch, names)
        if witness_status != 'sat':
            raise ProofError('Could not reproduce satisfiable counterexample')
        values = dict(sexpr('\n'.join(answer.splitlines()[1:])))
        witness = {
            'initial_registers': [number(values[name]) for name in inputs],
            'initial_nzcv': sum((8 >> i) for i, name in enumerate(flags) if values[name] == 'true'),
            'read_responses_hex': bytes(number(values[name]) for name in responses).hex(),
            'reference_final_registers': [number(values[name]) for name in left],
            'candidate_final_registers': [number(values[name]) for name in right],
        }
        (output / 'counterexample.smt2').write_text(problem.script(mismatch, names))

    obligations = '\n'.join(problem.lines) + '\n'
    for query in problem.queries:
        obligations += '(push 1)\n(assert ' + query['condition'] + ')\n(check-sat)\n(pop 1)\n'
    (output / 'obligations.smt2').write_text(obligations)
    (output / 'obligations.json').write_text(json.dumps(problem.queries, indent=2) + '\n')
    report = {
        'status': status,
        'equivalent_under_read_event_contract': status == 'unsat',
        'return_value_difference_status': return_status,
        'scope': 'checksum function, full R0-R14/NZCV at every instruction boundary, relative PC, ordered byte reads and ordinary return target',
        'pointer_domain': 'all 32-bit values, including address wrap',
        'return_domain': 'initial LR is odd and 0x101 <= LR < 0xfff8; ordinary Thumb return into MAIN flash',
        'read_response_domain': 'independent arbitrary 8-bit response at each read; shared between executions',
        'first_read_failure_relation': 'all pre-read checkpoints compared; same environment failure after any successful response prefix',
        'original_address': 0x282c, 'candidate_address': base,
        'original_bytes': original.hex(), 'candidate_bytes': code.hex(),
        'binaries_identical': original == code,
        'reference_steps': reference.steps, 'candidate_steps': candidate.steps,
        'reference_reads': len(reference.reads), 'candidate_reads': len(candidate.reads),
        'instruction_boundaries_compared': min(len(reference.states), len(candidate.states)),
        'branch_directions_proved': len(reference.branches) + len(candidate.branches),
        'solver_obligations': len(problem.queries),
        'reference_sha256': EXPECTED,
        'solver': subprocess.check_output(['z3', '-version'], text=True).strip(),
        'proof_inputs_sha256': proof_inputs,
        'witness': witness,
        'whole_firmware_equivalence': False,
        'physical_symbol_bound': False,
        'limitations': [
            'Code fetches must succeed and remain immutable; execution is Thumb outside an IT block with no asynchronous exceptions.',
            'The environment response relation is a premise, not proof that arbitrary original/rebuilt memory contents agree.',
            'Read failure is observed before the faulting load; physical fault entry, literal saved PC and handlers are not proved equivalent.',
            'Relative PC correspondence does not preserve observable original code addresses.',
            'Instruction-boundary equality is not a physical-cycle, flash-wait-state, interrupt or silicon theorem.',
            'The manually modeled instruction subset and SMT solver remain trusted components.',
        ],
    }
    if any(digest(ROOT / name) != expected for name, expected in proof_inputs.items()):
        raise ProofError('Proof implementation changed during execution')
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def prove(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    for name in ('report.json', 'physical-build-manifest.json'):
        (output / name).unlink(missing_ok=True)
    build_tools = {name: digest(ROOT / name) for name in (
        'tools/build_physical_firmware.py', 'tools/build_target_interfaces.py')}
    manifest = build(output / 'physical-image')
    elf = output / 'physical-image/firmware.elf'
    binary = output / 'physical-image/firmware.bin'
    if manifest['status'] != 'linked-experimental' or not manifest['inputs_unchanged_during_build']:
        raise ProofError('No successful stable physical source build')
    if manifest['unresolved_symbols'] or manifest['layout_audit']['issues']:
        raise ProofError('Physical source build failed layout/link audit')
    manifest_path = output / 'physical-image/manifest.json'
    snapshots = {path: path.read_bytes() for path in (elf, binary, manifest_path)}
    if json.loads(snapshots[manifest_path]) != manifest:
        raise ProofError('Build manifest changed after compilation')
    artifact_hashes = {path: hashlib.sha256(data).hexdigest() for path, data in snapshots.items()}
    if artifact_hashes[elf] != manifest['elf_sha256'] or artifact_hashes[binary] != manifest['binary_sha256']:
        raise ProofError('Physical artifacts do not match build manifest')
    code, base = extract_function(snapshots[elf], 'syscon_cfg_checksum')
    if snapshots[binary][base:base + len(code)] != code:
        raise ProofError('Linked symbol bytes differ from physical flash image')
    report = compare(code, base, output)
    # Reject source drift across both compilation and proof generation.
    for name, expected in manifest['build_input_sha256'].items():
        if digest(ROOT / name) != expected:
            raise ProofError('Source changed during proof: ' + name)
    if any(digest(ROOT / name) != expected for name, expected in build_tools.items()):
        raise ProofError('Build implementation changed during proof')
    if any(digest(path) != expected for path, expected in artifact_hashes.items()):
        raise ProofError('Physical artifact changed during proof')
    report.update({
        'candidate_symbol': 'syscon_cfg_checksum',
        'candidate_elf_sha256': artifact_hashes[elf],
        'candidate_binary_sha256': artifact_hashes[binary],
        'build_manifest_sha256': artifact_hashes[manifest_path],
        'physical_build_inputs_sha256': manifest['build_input_sha256'],
        'compiler': subprocess.check_output(['arm-none-eabi-gcc', '--version'], text=True).splitlines()[0],
        'build_tools_sha256': build_tools,
        'physical_symbol_bound': True,
    })
    # Preserve the build evidence without versioning intermediate objects or
    # presenting an experimental linked image as a distributable firmware.
    (output / 'physical-build-manifest.json').write_bytes(snapshots[manifest_path])
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'analysis/proof-physical-checksum')
    args = parser.parse_args()
    print(json.dumps(prove(args.output), indent=2))
