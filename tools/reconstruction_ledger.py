"""Curated reconstruction inventory. Instruction exercise is an independent axis.

The map is reviewed against C implementations, module docs, and decompilation;
address mentions or hook entries alone are never treated as implementations.
"""
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from coverage_report import input_hashes

ROOT = Path(__file__).resolve().parents[1]
MAP = {}

def register(module, entries, status='reconstructed_bounded', note='', source=None, tests=None, doc=None):
    for token in entries.split():
        address = int(token, 16)
        assert address not in MAP, hex(address)
        MAP[address] = dict(module=module, semantic_status=status,
            source=source or f'src/{module}.c',
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
register('fault_handlers','79e4 7bb8 7bcc',source='target/fault_handlers.c',note='Compiled Cortex-M0+ candidate compared with original bounded halt execution; hardfault/NMI also have host fault_control adapters.')
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
register('core_helpers','74f8 7ae8',source='target/core_helpers.c',note='Target ARM tests compare sleep sequencing with explicit wake/log boundaries and exact delay instructions; no physical timing claim.')

register('format_wrappers','8f88 8fa0 92f4',source='target/format_wrappers.c',tests=['tests/test_arm_rebuild.py'],doc='docs/arm-rebuild.md',note='Recompiled Cortex-M0+ wrappers compare observable output; incidental return registers and exact bytes not claimed.')
MAP[0x5edc]['additional_sources']=['target/format_wrappers.c']
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
    MAP[address]['additional_sources']=['src/runtime_arithmetic.c','target/runtime_arithmetic_abi.S','target/runtime_arithmetic_float.c']
register('runtime_support','969c 96aa 96b8 971c 9a40 9a54 a828 a8ac a8ae a8c6',source='target/runtime_support.c',
    tests=['tests/test_runtime_support.py','tests/test_runtime_support_integration.py'],
    note='Image-specific locale/reent/weak-exit behavior and original wrappers; direct ARM plus source-only linked integration.')
register('runtime_heap','a8ec a980 aa3c aa88 aaac aabc aacc',source='target/runtime_heap.c',
    note='Original allocator metadata, 32-bit pointers and overread behavior; real image sbrk failure and separate scripted backing tests.')
register('runtime_stdio','9a60 9d24 9d9c a0d4 a1b4 a714 a830',source='target/runtime_stdio.c',
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



def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    functions=list(csv.DictReader((ROOT/'analysis/functions.tsv').open(),delimiter='\t'))
    ranges=list(csv.DictReader((ROOT/'analysis/function-ranges.tsv').open(),delimiter='\t'))
    listing={int(line.split()[0],16) for line in (ROOT/'analysis/listing.txt').read_text().splitlines()}
    coverage=json.loads((ROOT/'analysis/full-suite-checkpoint.json').read_text())
    initial_inputs=coverage.get('input_sha256')
    changed_since_checkpoint=[] if initial_inputs is not None else None
    if initial_inputs is not None:
        current_inputs=input_hashes()
        changed_since_checkpoint=sorted(path for path in set(initial_inputs)|set(current_inputs) if initial_inputs.get(path)!=current_inputs.get(path))
    executed={int(a,16) for a in coverage['executed_original_addresses']}
    hooks={int(a,16) for a in coverage['replaced_endpoint_addresses']}
    fingerprints=json.loads((ROOT/'analysis/runtime-fingerprints.json').read_text())
    comparisons=[('analysis/binary-comparison.json',json.loads((ROOT/'analysis/binary-comparison.json').read_text()))]
    extra=ROOT/'analysis/core-helper-binary-comparison.json'
    if extra.exists():comparisons.append(('analysis/core-helper-binary-comparison.json',json.loads(extra.read_text())))
    runtime_path='analysis/runtime-memory-binary-comparison.json'
    runtime_comparison=json.loads((ROOT/runtime_path).read_text())
    assert runtime_comparison['reference_sha256']==coverage['reference_sha256']
    assert runtime_comparison['source_sha256']==sha(ROOT/'src/runtime_memory.c'), 'stale runtime binary comparison'
    comparisons.extend((runtime_path,row) for row in runtime_comparison['functions'])
    arithmetic_path='analysis/runtime-arithmetic-binary-comparison.json'
    arithmetic_comparison=json.loads((ROOT/arithmetic_path).read_text())
    assert arithmetic_comparison['reference_sha256']==coverage['reference_sha256']
    for source,digest in arithmetic_comparison['source_sha256'].items():
        assert sha(ROOT/source)==digest, f'stale arithmetic binary comparison: {source}'
    for row in arithmetic_comparison['functions']:
        comparisons.append((arithmetic_path,dict(row,function=row['symbol'],
            original_size=row['original_extent_bytes'],reconstructed_size=row['rebuilt_size'])))
    proof_path='analysis/proof-checksum/report.json'
    proof=json.loads((ROOT/proof_path).read_text())
    assert proof['reference_sha256']==coverage['reference_sha256']
    assert proof['source_sha256']==sha(ROOT/'src/config.c')
    assert proof['proof_tool_sha256']==sha(ROOT/'tools/proof_checksum.py')
    assert proof['project_header_sha256']==sha(ROOT/'include/syscon.h')
    assert proof['status']=='unsat' and proof['contract_satisfiable']
    assert coverage['pytest_exitstatus']==0, 'coverage checkpoint is not successful'
    for _,comparison in comparisons:
        if comparison['exact_bytes']:
            assert not comparison.get('unresolved_relocations'), 'unresolved relocation cannot prove exact linked bytes'
            assert comparison['original_size']==comparison['reconstructed_size']
    rows=[]
    for f in functions:
        address=int(f['address'],16)
        fr=[(int(r['start'],16),int(r['end_inclusive'],16)) for r in ranges if r['function']==f['address']]
        instructions={i for lo,hi in fr for i in listing if lo<=i<=hi}
        semantic=MAP.get(address)
        if semantic is None:
            if address in GAPS:
                label,note=GAPS[address]
                semantic=dict(module=label,semantic_status='unimplemented',source=None,module_tests=[],documentation=None,note=note)
            else:
                assert address<0x2678 or address>=0x969c, f'unmapped application/HAL entry requires review: {address:#x}'
                semantic=dict(module='runtime_candidate',semantic_status='unreconstructed_runtime_candidate',source=None,module_tests=[],documentation=None,
                    note='Placement/decompilation suggests compiler/libc support; identity and complete replacement remain unverified. Host libc or minimal test runtime use does not reconstruct this routine.')
        candidates=[dict(m) for m in fingerprints['matches'] if int(m['address'],16)==address]
        if address in (0x8f88,0x92f4):
            for m in candidates:m['identity_assessment']='rejected_generic_wrapper_match'
        else:
            for m in candidates:
                m['identity_assessment']='candidate_not_proven'
                if m['size']<32 or not m['unique_match']:m['identity_caution']='Short or nonunique sequence; verify call/data relocation targets before assigning symbol.'
        exact=dict(reconstructed_function_match=False,whole_firmware_match=False)
        for evidence,comparison in comparisons:
            match_address=comparison['original_address']
            if isinstance(match_address,str):match_address=int(match_address,16)
            if address==match_address:
                exact.update(reconstructed_function_match=bool(comparison['exact_bytes']) and not comparison.get('unresolved_relocations',[]),evidence=evidence,function=comparison['function'],unresolved_relocations=comparison.get('unresolved_relocations',[]))
        rows.append(dict(address=hex(address),identified_name=f['name'],identified_body_bytes=int(f['bytes']),
            static_ranges=[[hex(a),hex(b)] for a,b in fr],**semantic,
            work_in_progress='parent implementing; validation pending' if address in PENDING_ROOT else None,
            original_instruction_exercise=dict(checkpoint='analysis/full-suite-checkpoint.json',denominator='current hashed listing and function ranges; observed address set from historical checkpoint',identified=len(instructions),exercised=len(instructions&executed),
                entry_observed=address in executed,entry_hooked_in_some_tests=address in hooks,
                status='all_identified_exercised' if instructions and instructions<=executed else 'partially_exercised' if instructions&executed else 'not_exercised'),
            exact_binary=exact,runtime_fingerprints=candidates,hardware_validation='not_performed'))
    assert len({r['address'] for r in rows})==len(functions)
    assert not(set(MAP)-{int(f['address'],16) for f in functions}), 'curated entries missing from current static inventory'
    inputs=['analysis/functions.tsv','analysis/function-ranges.tsv','analysis/listing.txt','analysis/full-suite-checkpoint.json','analysis/runtime-fingerprints.json','analysis/binary-comparison.json']
    inputs += ['analysis/runtime-scan-mapping.json',*TARGET_MAPPING_FILES,proof_path,'analysis/proof-checksum-negative/report.json','analysis/proof-checksum-checkpoint.json']
    inputs += [evidence for evidence,_ in comparisons if evidence not in inputs]
    inputs+=sorted({r['source'] for r in rows if r['source']})
    inputs+=sorted({p for r in rows for p in r.get('additional_sources',[])})
    inputs+=sorted({p for r in rows for p in r.get('additional_documentation',[])})
    inputs+=sorted({p for r in rows for p in r['module_tests']})
    inputs+=sorted({r['documentation'] for r in rows if r['documentation']})
    for p in inputs:assert (ROOT/p).is_file(),p
    unidentified_matches=[m for m in fingerprints['matches'] if int(m['address'],16) not in {int(f['address'],16) for f in functions}]
    ram_reports=[]
    for path in sorted((ROOT/'analysis/coverage-runs').glob('*.json')):
        j=json.loads(path.read_text())
        if j.get('pytest_exitstatus')!=0 or j.get('reference_sha256')!=coverage['reference_sha256']:continue
        ram=sorted({int(a,16) for a in j['executed_original_addresses'] if 0x20000000<=int(a,16)<0x2000002c})
        if ram:ram_reports.append(dict(report=str(path.relative_to(ROOT)),sha256=sha(path),executed_ram_addresses=[hex(a) for a in ram]))
    artifact=dict(schema_version=1,generated_utc=datetime.now(timezone.utc).isoformat(),reference_sha256=coverage['reference_sha256'],
        summary=dict(identified_functions=len(rows),semantic_status_counts=dict(Counter(r['semantic_status'] for r in rows)),
            exercise_status_counts=dict(Counter(r['original_instruction_exercise']['status'] for r in rows)),
            exact_reconstructed_function_matches=sum(r['exact_binary']['reconstructed_function_match'] for r in rows),hardware_validated_functions=0,newly_audited_target_entries=sum('target_abi' in r for r in rows),scoped_solver_proofs=1),
        snapshot_inputs=[dict(path=p,sha256=sha(ROOT/p)) for p in dict.fromkeys(inputs)],
        coverage_checkpoint=dict(path='analysis/full-suite-checkpoint.json',sha256=sha(ROOT/'analysis/full-suite-checkpoint.json'),pytest_exitstatus=coverage['pytest_exitstatus'],
            test_counts=coverage.get('test_counts'),initial_input_sha256=initial_inputs,
            inputs_unchanged_during_run=coverage.get('inputs_unchanged_during_run'),
            changed_since_checkpoint=changed_since_checkpoint,
            current_code_matches_passed_snapshot=(not changed_since_checkpoint and coverage.get('inputs_unchanged_during_run') is True) if initial_inputs is not None else None,
            invocation=coverage['invocation'],note='Recorded full-suite invocation; input hashes identify this inventory snapshot. Later source edits require another run, not inferred success.'),
        definitions=dict(reconstructed_bounded='Semantic C implementation with explicit module scope, dependencies and unsupported domains; neither complete behavior proof nor ABI/binary equivalence.',
            folded_caller_domain='Original helper effects incorporated in caller C for its validated domain; standalone target helper ABI or arbitrary input domain remains incomplete.',
            unimplemented='Known app/HAL/wrapper body absent from replacement; original execution or hooks do not fill this gap.',
            unreconstructed_runtime_candidate='No complete audited source replacement. Fingerprints are evidence candidates only, and identities may be ambiguous.'),
        known_static_analysis_exceptions=[
            dict(kind='copied_ram_code',image_start='0xaaf0',runtime_start='0x20000000',code_size_bytes=44,copied_size_bytes=48,veneer='0xaae0',source='src/flash_controller.c',tests=['tests/test_flash_controller.py'],
                 note='RAM instructions are not members of the identified flash function inventory. Final four copied bytes are the STATCMD offset literal. Successful scoped reports below record execution separately.',scoped_evidence=ram_reports),
            dict(kind='previously_missing_formatter_block',addresses=[hex(a) for a in [0x9256,0x9258,0x925a,0x925c,0x925e,0x9260,0x9262,0x9266,0x9268]],owner='0x9038',source='src/format.c',
                 currently_missing_from_listing=[hex(a) for a in [0x9256,0x9258,0x925a,0x925c,0x925e,0x9260,0x9262,0x9266,0x9268] if a not in listing],
                 note='Original %p branch discovered by execution; static inventory refresh may include it after this checkpoint.')],
        scoped_solver_proofs=[dict(address='0x282c',symbol='syscon_checksum31',source='src/config.c',evidence=proof_path,contract=proof['scope'],status=proof['status'],whole_domain_equivalence=False,whole_firmware_equivalence=False)],
        runtime_matches_without_identified_function_entry=unidentified_matches,
        global_limitations=['No completion percentage is calculated. Semantic reconstruction, instruction exercise, byte matches, and hardware validation are different evidence axes.',
            'Identified runtime entries now have scoped source replacements; full target image integration, complete board emulation, and physical validation remain incomplete. No flash candidate exists.',
            'Dynamic hook-address lists are unions across tests: an entry may be hooked in one test and execute genuinely in another.',
            'All identified-instruction coverage is not branch/path/domain completeness and can miss undiscovered code, interrupts, timing and corrupt-state behavior.',
            'Runtime fingerprints from installed archives are separate from the nine reconstructed-source exact body matches. Masked relocation fields have not been validated.',
            'Host adapters may suppress logs or replace fatal calls with sentinels; module documentation defines the tested boundary.',
            'Snapshot source/test hashes detect later edits; regenerate and review mappings when modules change.'],functions=rows,
        complete_reconstruction=False,full_board_emulation=False,flash_candidate=False)
    (ROOT/'analysis/reconstruction-ledger.json').write_text(json.dumps(artifact,indent=2)+'\n')
    write_markdown(artifact)
    print(json.dumps(artifact['summary'],indent=2))


def write_markdown(ledger):
    lines=['# Reconstruction ledger','',
        'This is a function-by-function evidence inventory, not a completion percentage. The machine-readable companion is `analysis/reconstruction-ledger.json`; regenerate with `python3 tools/reconstruction_ledger.py` after reviewing the curated mapping when implementations change.','',
        f'The current static inventory contains {ledger["summary"]["identified_functions"]} identified functions. Their semantic states are:','',
        '| State | Count |','| --- | ---: |']
    for k,n in ledger['summary']['semantic_status_counts'].items():lines.append(f'| {k} | {n} |')
    lines+=['','“Reconstructed” means a scoped C adapter exists. It does not mean every input/path, original ABI, exact machine bytes, or board behavior is verified. “Folded” helpers are implemented only as effects within their tested callers, not complete generic entry points. All currently identified runtime candidates now have scoped replacements; undiscovered code and unsupported domains are not implied complete.','',
        '## Independent evidence axes','',
        '- Semantic mapping points to actual C sources, module tests, and scope documentation. Unreviewed Ghidra output and endpoint hooks do not count as replacement code.',
        '- Original instruction exercise uses observed addresses from the pinned successful `analysis/full-suite-checkpoint.json` invocation, recomputed against the current hashed listing/ranges. Counts can differ from that report after static-analysis corrections. The snapshot may precede recent additions: a reconstructed routine with zero exercise at that checkpoint is not automatically unimplemented. Module tests and later scoped reports supply separate evidence.',
        '- Nine rebuilt bodies have exact bytes: checksum `0x282c` (20 bytes), delay `0x7ae8` (10), memset `0x975a` (16), strchr `0x9828` (28), switch dispatch `0xc0` (18), `0xd4` (18), `0x2660` (20), divide-by-zero `0x3d0` (2), and float-to-int `0x135c` (64). Unresolved relocations disqualify strrchr. These isolated matches do not establish whole-firmware binary equivalence. Runtime archive fragments are listed separately; a short relocation-masked match does not establish identity. In particular, matches identifying `0x8f88` and `0x92f4` as newlib I/O routines are rejected generic-wrapper matches.',
        '- The `target_abi` records identify newly audited standalone target interfaces; they do not certify all input domains or complete target linkage. The checksum has a solver-checked theorem under the explicit SRAM/sequential/AAPCS contract in `docs/equivalence-proof.md`; that theorem does not prove all firmware calls or the whole image.',
        '- Hardware validation is `not_performed` for every ledger entry. No complete target image or safe flash candidate is produced.','',
        'The JSON includes hashes of every mapped source/test/document and static/coverage inputs. When the test checkpoint records initial code/test/tool hashes, the ledger checks whether inputs stayed unchanged during the run and still match current files; a missing historical hash record remains unverified.','',
        f'Checkpoint test counts: `{ledger["coverage_checkpoint"]["test_counts"]}`. Inputs unchanged during the run: `{ledger["coverage_checkpoint"]["inputs_unchanged_during_run"]}`. Current code matches that passed snapshot: `{ledger["coverage_checkpoint"]["current_code_matches_passed_snapshot"]}`.','',
        '## Known application and HAL gaps','',
        '| Entry | Missing behavior |','| --- | --- |']
    for r in ledger['functions']:
        if r['semantic_status']=='unimplemented':
            pending=' **Implementation in progress; validation pending.**' if r['work_in_progress'] else ''
            lines.append(f'| `{r["address"]}` | {r["note"]}{pending} |')
    if not any(r['semantic_status']=='unimplemented' for r in ledger['functions']):
        lines.append('| — | Every currently identified app/HAL entry has a scoped or caller-folded implementation. This does not cover arbitrary helper domains or full target integration. |')
    lines+=['','All currently identified compiler/libc runtime entries have source replacements and direct ARM comparisons. Arithmetic, memory, support, heap, stdio, and scan/printf scope is documented separately. The runtime builds use reviewed source rather than installed libc/libgcc archives. This does not prove complete path coverage or full-image ABI integration.','',
        '## Static inventory exceptions','',
        'FLASHCTL executes 44 instruction bytes copied from image `0xaaf0` to SRAM `0x20000000`, with a four-byte literal following them. The `0xaae0` veneer is identified, but the RAM body is not an extra flash function in the identified flash-function inventory. The JSON separately records successful scoped reports containing its actual RAM instruction addresses. Its modeled status/polling behavior is in `src/flash_controller.c` and `docs/flash-controller.md`.',
        '',
        'Execution also discovered the `%p` block at `0x9256..0x9268`, previously missing from Ghidra\'s listing. It belongs to formatter `0x9038`; the JSON records which instruction addresses remain absent from the current listing. Updated static analysis can change counts without changing replacement correctness. Runtime fingerprints at non-entry/interior addresses are retained separately for future boundary review.','',
        '## Every identified function','',
        '`Exercise` is exercised/identified instruction addresses in the checkpoint, not semantic completion. `C` is a scoped replacement; `folded` is only its caller domain; `missing` is a known app/HAL gap; `runtime` is an unreconstructed runtime candidate.','',
        '| Entry | Static name | Semantic state | Source | Exercise |','| --- | --- | --- | --- | ---: |']
    labels={'reconstructed_bounded':'C','folded_caller_domain':'folded','unimplemented':'missing','unreconstructed_runtime_candidate':'runtime'}
    for r in ledger['functions']:
        e=r['original_instruction_exercise'];source=f'`{r["source"]}`' if r['source'] else '—'
        lines.append(f'| `{r["address"]}` | `{r["identified_name"]}` | {labels[r["semantic_status"]]} | {source} | {e["exercised"]}/{e["identified"]} |')
    (ROOT/'docs/reconstruction-ledger.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':main()
