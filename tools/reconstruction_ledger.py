"""Curated reconstruction inventory. Instruction exercise is an independent axis.

The map is reviewed against C implementations, module docs, and decompilation;
address mentions or hook entries alone are never treated as implementations.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
from coverage_report import input_hashes
from build_physical_firmware import production_sources
from inventory import EXPECTED

ROOT = Path(__file__).resolve().parents[1]
MAP = {}
SHARED_SOURCES = {'runtime_memory': 'src/runtime/runtime_memory.c', 'runtime_arithmetic': 'src/runtime/runtime_arithmetic.c', 'format': 'src/runtime/format.c', 'flash_controller': 'src/drivers/flash_controller.c'}

def register(module, entries, status='reconstructed_bounded', note='', source=None, tests=None, doc=None):
    source = source or SHARED_SOURCES.get(module, f'tests/models/{module}.c')
    for token in entries.split():
        address = int(token, 16)
        assert address not in MAP, hex(address)
        MAP[address] = dict(module=module, semantic_status=status,
            source=source, legacy_model=source if source.startswith('tests/') else None,
            module_tests=tests or [f'tests/test_{module}.py'],
            documentation=doc or f'docs/{module.replace("_", "-")}.md', note=note)

register('config','27a8 27dc 2810 282c 2840 28d4 296c 29a0 2abc 2cb8 2d08 2d94 2df8 2f0c 2fa0 32c8',
    note='Store/context host adapter; diagnostic and fatal boundaries and corrupt-format unsupported domain documented.',
    tests=['tests/test_differential.py','tests/test_config_updates.py'],doc='docs/config-reconstruction.md')
register('config_commands','3fdc 4490 44dc 4528 45e0 45ec 45f8 4638 4684 46d4 4714 4760',doc='docs/config-reconstruction.md')
register('config_commands','3048 3098 30c0 30e8 30ec 31d0 3278 3298 32b0 339c 33b4 3464',
    status='folded_caller_domain',note='Behavior folded into find/dump/config dispatch; no standalone original-ABI entry. Constants/blank queries only validated in command/store domains.',doc='docs/config-reconstruction.md')
register('diagnostics','3114 3120 312c 3138 3144 3150 315c 3178 3194 347c 3488')
register('application','3610 3a8c 3ad4 3af4 3b0c 3b34 3ec0 4c14 78ac 7910 7928 7974 96d4',
    note='Host main is split into init/tick; external calls remain explicit dependencies. Constructors use known image array.')
register('ioexpander','3620 364e 3668 36bc 374c 379c 37e4 3808 386c 3940 39e8')
register('control_commands','3ef0 3f24 3f80 3fd0 40a0 40fc 4110 41a4 422c 4258 42c8 4320 4364 4420 47b0 47bc 47fc 4850 48a4 48e0 4904 4970 49ac',
    note='Explicit dependencies; raw printf tokens without arguments retain unsupported-stack boundary.')
register('protocol','49d0',tests=['tests/test_differential.py','tests/test_config_commands.py','tests/test_control_commands.py'],doc='docs/control-commands.md')
register('protocol','3f08',status='folded_caller_domain',note='Failure printer folded into parser failure().',tests=['tests/test_differential.py'],doc='docs/control-commands.md')
register('power_manager','4c50 4ca8 4d00 4d58 4d68 4d9c 4df4 4e04 4e34 4ec4 4ed4 4ee0 4fd0 5004 5048 50f4 5148 517c 51c0 5264 5274')
register('power_policy','5358 54cc 559c 55b4 55c4 55dc 562c 5638 5670 567c 5694')
register('power_key','570c 5740 5844 5908 591c 5970')
register('retained','59a0 59d8 5a88 5aa8 5ac4 5ad4 5af0 5afc 5b14',doc='docs/timers-retained.md')
register('rgb','5b20 5b48 5b7c 5bd4 5bfc 5c38 5c68 5cac 5dbc 5dc8 5df4 5e0c 5e24')
register('sg560d','5e30 5f30 614c 61b8 61d0 61f0 6210 6230 6238 6240 6248 6282 62ec 6384 6428 64a0 6520 65d0 65da 65e4 65f0 6650 6690 66a0 66bc 6720 6838 68a4 68fc 6948 6a28 6a48 6a68 7468 7488 74a8 74c8')
register('tasks','7540 7554 75d8 76d8',doc='README.md')
register('timers','76f8 776c 77b4 77c0 77fc 781c 7880',doc='docs/timers-retained.md')
register('mspm0_core','798c 79d0 79f0 7a50 7a54 7c08 7c3c 7f58 8054 80ac 80f8 8148 81f8 8258',
    note='Passive register/callback model; invalid GPIO input may return host rejection at assertion boundary.')
register('fault_control','2678 7b78 7b88 7b9c 7be0 7bfc')
register('fault_handlers','79e4 7bb8 7bcc',source='src/drivers/fault_handlers.c',note='Compiled Cortex-M0+ candidate compared with original bounded halt execution; hardfault/NMI also have host fault_control adapters.')
register('flash_controller','2738 7af4 7b10 7b44 7b60 aae0',note='0xaae0 veneer is folded into the reconstructed copied-RAM polling executor. No actual flash access.')
register('adc','7c54 7d54 7e7c 7f24')
register('adc','7a68 930c 9664 9688',status='folded_caller_domain',note='Lookup and driver effects folded into ADC caller for observed arguments; generic helper ABI/configurations not fully reconstructed.')
register('i2c','82b4 82f0 844c 860c 8798')
register('i2c','7ad4 934c 9374 93a0 93d0',status='folded_caller_domain',note='Lookup/clock/start/FIFO helper behavior folded into only configured controller paths; arbitrary helper configurations outside validated domain.')
register('pwm','87dc 88c0 9400 941c 942c 9450 9470 948c')
register('pwm','7a90',status='folded_caller_domain',note='Three-entry lookup folded into PWM board adapter; target pointer-return ABI absent.')
register('uart_hal','891c 8938 8954 8b50 95f0 9638')
register('uart_hal','7ac0',status='folded_caller_domain',note='Two-port lookup folded into board adapter; target pointer-return ABI absent.')
register('uart','8c34 8c8c 8cf0 8d70 8de4')
register('uart','964c',status='folded_caller_domain',note='Polling transmit helper folded into put(); only configured UART ports represented.')
register('logging','5edc 8e8c',doc='docs/formatting.md')
register('format','8fcc 9038 92ac',doc='docs/formatting.md')
register('format','9012 9026',status='folded_caller_domain',note='Output/no-op callbacks folded into buffer and null-output formatter paths; no target callback ABI.',doc='docs/formatting.md')

register('application_glue','30f0 4c24 74e8 76f0 8e6c 8e7c 8fc0',note='Seven wrappers integrated with existing config/GPIO/UART bodies; six differential cases passed; host context ABI.')
register('core_helpers','74f8 7ae8',source='src/drivers/core_helpers.c',note='Target ARM tests compare sleep sequencing with explicit wake/log boundaries and exact delay instructions; no physical timing claim.')

register('format_wrappers','8f88 8fa0 92f4',source='tests/fixtures/target/format_wrappers.c',tests=['tests/test_arm_rebuild.py'],doc='docs/arm-rebuild.md',note='Recompiled Cortex-M0+ wrappers compare observable output; incidental return registers and exact bytes not claimed.')
MAP[0x5edc]['additional_sources']=['tests/fixtures/target/format_wrappers.c']
MAP[0x5edc]['additional_documentation']=['docs/arm-rebuild.md']
MAP[0x5edc]['module_tests'].append('tests/test_arm_rebuild.py')

PENDING_ROOT = set()

register('format','9028',tests=['tests/test_format_callback.py'],doc='docs/formatting.md',note='Direct callback count/argument adapter; original target callback pointer and context preserved.')
MAP[0x9038]['module_tests'].append('tests/test_format_callback.py')
MAP[0x9038]['note']='Both bounded and generic callback output interfaces implemented; private stack corruption/recursion and unavailable target memory remain explicit limits.'
register('runtime_memory','263c 2650 972c 9748 975a 9828 9890 98b4 98dc a8b0',note='Recompiled ARM differential tests compare returns and full memory; original strrchr full-int/byte truncation fault behavior preserved. Corrupt/wrapping pointers outside scope.')
# Runtime entries have source-only target builds and direct original-ARM comparisons.
from runtime_arithmetic_mappings import MAPPINGS as ARITHMETIC_MAPPINGS
for address,(symbol,source) in ARITHMETIC_MAPPINGS.items():
    register('runtime_arithmetic',f'{address:x}',source=source,
        note=f'{symbol}: AAPCS/flags adapters and pinned GCC soft-fp source; documented arithmetic domains and unreachable guards.',
        tests=['tests/test_runtime_arithmetic.py'],doc='docs/runtime-arithmetic.md')
    MAP[address]['additional_sources']=['src/runtime/runtime_arithmetic.c','src/runtime/runtime_arithmetic_abi.S','src/runtime/runtime_arithmetic_float.c']
register('runtime_support','969c 96aa 96b8 971c 9a40 9a54 a828 a8ac a8ae a8c6',source='src/runtime/runtime_support.c',
    tests=['tests/test_runtime_support.py','tests/test_runtime_support_integration.py'],
    note='Image-specific locale/reent/weak-exit behavior and original wrappers; direct ARM plus source-only linked integration.')
register('runtime_heap','a8ec a980 aa3c aa88 aaac aabc aacc',source='src/runtime/runtime_heap.c',
    note='Original allocator metadata, 32-bit pointers and overread behavior; real image sbrk failure and separate scripted backing tests.')
register('runtime_stdio','9a60 9d24 9d9c a0d4 a1b4 a714 a830',source='src/runtime/runtime_stdio.c',
    note='Original FILE/reent layout, callback ABI and stream/error behavior; source-only ARM integration.')
scan_mapping=json.loads((ROOT/'analysis/runtime-scan-mapping.json').read_text())
for entry in scan_mapping['entries']:
    register('runtime_scan',entry['address'],source=entry['source'],tests=[entry['tests']],doc=entry['docs'],
        note=entry['symbol']+': source-only linked ARM comparison; original printf incoming-stack seeds preserved by ABI shims.')
    MAP[int(entry['address'],16)]['additional_sources']=scan_mapping['dependencies']
# Explicit target-entry evidence is separate from the historical host adapter.
TARGET_MAPPING_FILES=['analysis/callback-helper-mapping.json','analysis/hal-helper-mapping.json',
    'analysis/config-helpers-mapping.json','analysis/uart-ring-target-mapping.json',
    'analysis/fault-control-target-mapping.json','analysis/mspm0-core-target-mapping.json',
    'analysis/adc-uart-target-mapping.json','analysis/scheduling-target-mapping.json',
    'analysis/diagnostics-target-mapping.json','analysis/application-target-mapping.json',
    'analysis/logger-target-mapping.json','analysis/power-key-target-mapping.json','analysis/rgb-target-mapping.json',
    'analysis/i2c-pwm-target-mapping.json','analysis/power-policy-target-mapping.json',
    'analysis/ioexpander-target-mapping.json','analysis/power-manager-target-mapping.json',
    'analysis/protocol-target-mapping.json','analysis/config-commands-target-mapping.json',
    'analysis/config-update-target-mapping.json','analysis/flash-abi-target-mapping.json',
    'analysis/control-commands-target-mapping.json','analysis/format-core-target-mapping.json',
    'analysis/sg560d-target-mapping.json','analysis/physical-startup-mapping.json']
for mapping_path in TARGET_MAPPING_FILES:
    mapping=json.loads((ROOT/mapping_path).read_text())
    for entry in mapping['entries']:
        address=int(entry['address'],16);row=MAP[address]
        source=entry.get('source',mapping.get('source'))
        test=entry.get('tests',mapping.get('tests'));doc=entry.get('docs',mapping.get('docs'))
        row['target_abi']=dict(symbol=entry['symbol'],source=source,tests=test,documentation=doc,
            mapping=mapping_path,status='tested_standalone_entry',
            scope=entry.get('proof_scope','See module documentation for dependencies, observation boundaries and unproven domains.'),
            whole_domain_equivalence=False,physical_image_integration=False)
        row.setdefault('additional_sources',[])
        if source not in row['additional_sources']:row['additional_sources'].append(source)
        row.setdefault('additional_documentation',[])
        if doc not in row['additional_documentation']:row['additional_documentation'].append(doc)
        for item in (test if isinstance(test,list) else [test]):
            if item not in row['module_tests']:row['module_tests'].append(item)
        for item in entry.get('additional_sources',[]):
            if item not in row['additional_sources']:row['additional_sources'].append(item)
        if row['semantic_status']=='folded_caller_domain':
            row['additional_sources'].append(row['source'])
            row['source']=source;row['semantic_status']='reconstructed_bounded'
            row['documentation']=doc
            row['note']='Standalone original-ABI target body now exists; former caller-folded implementation remains separate evidence. Full-domain proof and physical image integration remain unproved.'
GAPS = {}



def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def checkpoint_status(path, current_inputs):
    """Bind an optional test invocation to its exact inputs, never infer coverage."""
    if path is None:
        return {'status': 'not_supplied'}
    checkpoint = json.loads(Path(path).read_text())
    if checkpoint.get('reference_sha256') != EXPECTED:
        raise ValueError('Checkpoint uses a different reference firmware')
    initial = checkpoint.get('input_sha256')
    changed = None if initial is None else sorted(
        name for name in set(initial) | set(current_inputs)
        if initial.get(name) != current_inputs.get(name))
    if checkpoint.get('pytest_exitstatus') != 0:
        status = 'failed'
    elif initial is None or checkpoint.get('inputs_unchanged_during_run') is not True:
        status = 'unverified_inputs'
    elif changed:
        status = 'stale'
    else:
        status = 'passed_for_recorded_invocation'
    return dict(status=status, path=str(path), sha256=sha(Path(path)),
                invocation=checkpoint.get('invocation'),
                test_counts=checkpoint.get('test_counts'),
                changed_since_checkpoint=changed,
                note='Only the recorded invocation is covered; a quick or partial suite is not a full-suite result.')


def build_inventory(root=ROOT, mapping=None, sources=None):
    """Index curated function mappings against the actual production build list."""
    mapping = MAP if mapping is None else mapping
    sources = set(production_sources() if sources is None else sources)
    with (root / 'analysis/functions.tsv').open() as stream:
        functions = list(csv.DictReader(stream, delimiter='\t'))
    addresses = [int(row['address'], 16) for row in functions]
    if len(set(addresses)) != len(addresses) or set(addresses) != set(mapping):
        raise ValueError('Static function inventory and curated mapping disagree')
    rows = []
    paths = {'analysis/functions.tsv'}
    for function, address in zip(functions, addresses):
        model = mapping[address]
        target = model.get('target_abi', {})
        source = target.get('source', model['source'])
        if source not in sources:
            raise ValueError(f'{address:#x}: mapped source is not a production build input: {source}')
        tests = target.get('tests', model['module_tests'])
        tests = [tests] if isinstance(tests, str) else list(tests)
        documentation = target.get('documentation', model['documentation'])
        legacy = model['legacy_model']
        for relative in [source, *tests, documentation, *([legacy] if legacy else [])]:
            path = (root / relative).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file():
                raise ValueError(f'{address:#x}: missing or escaping mapped file: {relative}')
            paths.add(relative)
        rows.append(dict(address=hex(address), name=target.get('symbol', function['name']),
                         source=source, source_tree=source.split('/')[0],
                         build_input=True, semantic_scope=model['semantic_status'],
                         test_type='mapped ARM comparison' if target else 'mapped module tests',
                         tests=tests, documentation=documentation, legacy_model=legacy,
                         proof_status='not_assessed', hardware_status='not_assessed'))
    return dict(schema_version=2, reference_sha256=EXPECTED,
                summary=dict(identified_functions=len(rows),
                             sources_by_tree=dict(Counter(row['source_tree'] for row in rows))),
                functions=rows, mapped_file_sha256={name: sha(root / name) for name in sorted(paths)},
                limitations=[
                    'This is a source index, not proof of complete reconstruction or equivalent behavior.',
                    'A mapped file being a production build input does not establish that every function or path is linked and exercised.',
                    'Test files are mapped evidence entry points, not a claim that they passed in this invocation.',
                    'Proof and hardware status are not inferred from old generated reports. See the scoped proof tools and hardware record.',
                    'Static analysis can miss code; all identified functions is not all possible behavior.'])


def markdown(ledger):
    lines = ['# Firmware source inventory', '',
             'Generated from the current curated mappings and production build inputs. Test links identify where to validate a function; they do not report a passing test result.', '',
             f'Identified functions: {ledger["summary"]["identified_functions"]}. Checkpoint: `{ledger["checkpoint"]["status"]}`.', '',
             'Proof and hardware status are not assessed by this index. A supplied checkpoint covers only its recorded invocation.', '',
             '| Entry | Function | Tree | Source | Test type | Tests | Proof status |',
             '| --- | --- | --- | --- | --- | --- | --- |']
    for row in ledger['functions']:
        tests = ', '.join(f'`{test}`' for test in row['tests'])
        lines.append(f'| `{row["address"]}` | `{row["name"]}` | {row["source_tree"]} | `{row["source"]}` | {row["test_type"]} | {tests} | {row["proof_status"]} |')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/ledger')
    parser.add_argument('--checkpoint', type=Path,
                        help='Optional coverage report for one test invocation; stale inputs are reported explicitly')
    args = parser.parse_args()
    ledger = build_inventory()
    ledger['checkpoint'] = checkpoint_status(args.checkpoint, input_hashes())
    ledger['mapping_input_sha256'] = {name: sha(ROOT / name) for name in
        ['tools/reconstruction_ledger.py', 'tools/build_target_interfaces.py',
         'tools/build_physical_firmware.py', 'analysis/runtime-scan-mapping.json', *TARGET_MAPPING_FILES]}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'reconstruction-ledger.json').write_text(json.dumps(ledger, indent=2) + '\n')
    (args.output / 'reconstruction-ledger.md').write_text(markdown(ledger))
    print(json.dumps(dict(**ledger['summary'], checkpoint=ledger['checkpoint']['status'], output=str(args.output))))


if __name__ == '__main__':
    main()
