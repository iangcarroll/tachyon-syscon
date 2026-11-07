"""Recompute static ownership independently from dynamic execution evidence."""
import csv
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    paths=['analysis/listing.txt','analysis/functions.tsv','analysis/function-ranges.tsv',
           'analysis/full-suite-checkpoint.json','tools/AnnotateSyscon.java']
    listing={int(line.split()[0],16) for line in (ROOT/paths[0]).read_text().splitlines()}
    functions=list(csv.DictReader((ROOT/paths[1]).open(),delimiter='\t'))
    ranges=list(csv.DictReader((ROOT/paths[2]).open(),delimiter='\t'))
    owned={a for r in ranges for a in listing if int(r['start'],16)<=a<=int(r['end_inclusive'],16)}
    checkpoint=json.loads((ROOT/paths[3]).read_text())
    seen={int(a,16) for a in checkpoint['executed_original_addresses']}
    result=dict(input_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
        identified_functions=len(functions),listed=len(listing),owned=len(owned),
        exercised_listed=len(listing&seen),exercised_owned=len(owned&seen),
        unowned=[hex(a) for a in sorted(listing-owned)],
        exercised_unowned=[hex(a) for a in sorted((listing-owned)&seen)],
        note='Listed addresses may be data misclassified as code. Ownership is not exhaustive discovery or semantic verification.')
    (ROOT/'analysis/static-inventory-gaps.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('input_sha256','unowned')},indent=2))

if __name__=='__main__':main()
