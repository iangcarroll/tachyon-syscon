"""Report original instruction exercise, never equating it with verified equivalence."""
import csv
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from inventory import ROOT, EXPECTED

def input_hashes():
    paths=[ROOT/'Makefile',ROOT/'requirements.txt']
    for directory in ('src','include','tests','tools','vendor','references/ti-mspm0'):
        paths.extend(p for p in (ROOT/directory).rglob('*')
                     if p.is_file() and p.suffix in ('.c','.h','.S','.s','.py','.ld','.sh','.java','.svd','.json'))
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(paths) if p.is_file()}

def write_report(executed,hooks,exitstatus,initial_inputs=None,test_counts=None):
    instructions={int(line.split()[0],16) for line in (ROOT/'analysis/listing.txt').read_text().splitlines()}
    functions={r['address']:dict(address='0x'+r['address'],name=r['name'],instructions=set())
               for r in csv.DictReader((ROOT/'analysis/functions.tsv').open(),delimiter='\t')}
    for row in csv.DictReader((ROOT/'analysis/function-ranges.tsv').open(),delimiter='\t'):
        lo,hi=int(row['start'],16),int(row['end_inclusive'],16)
        functions[row['function']]['instructions'].update(a for a in instructions if lo<=a<=hi)
    rows=[]
    for f in functions.values():
        ins=f.pop('instructions')
        rows.append(dict(**f,identified_instructions=len(ins),exercised_instructions=len(ins&executed),
                         missing_instructions=[hex(a) for a in sorted(ins-executed)]))
    report=dict(reference_sha256=EXPECTED,invocation=sys.argv,pytest_exitstatus=int(exitstatus),
                test_counts=test_counts,input_sha256=initial_inputs,
                inputs_unchanged_during_run=(initial_inputs==input_hashes()) if initial_inputs is not None else None,
                identified_instruction_addresses=len(instructions),
                exercised_identified_instructions=len(instructions&executed),
                exercised_addresses_missing_from_static_listing=[hex(a) for a in sorted(executed-instructions) if a<0xf7f8],
                executed_original_addresses=[hex(a) for a in sorted(executed)],
                replaced_endpoint_addresses=[hex(a) for a in sorted(hooks)],functions=rows,
                complete_reconstruction=False,full_board_emulation=False,flash_candidate=False,
                limitations=['Only this pytest invocation is represented; partial test selections are partial coverage.',
                            'Discovered static instructions/functions may be incomplete or misclassified.',
                            'Executing a reference instruction is not proof that its C replacement is correct.',
                            'No branch/path completeness or hardware equivalence is claimed.'])
    encoded=json.dumps(report,indent=2)+'\n'
    runs=ROOT/'build/coverage-runs'
    runs.mkdir(parents=True,exist_ok=True)
    (runs/f'{time.time_ns()}-{os.getpid()}.json').write_text(encoded)
    destination=Path(os.environ.get('SYSCON_COVERAGE_OUTPUT',str(ROOT/'build/test-instruction-coverage.json')))
    destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_name(destination.name+f'.{os.getpid()}.tmp')
    temporary.write_text(encoded)
    temporary.replace(destination)
