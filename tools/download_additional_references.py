"""Download the additional repositories and datasheet-linked schematic sheets."""
import concurrent.futures
import json
from download_references import ROOT, DEST, download

inventories=json.loads((ROOT/'analysis/additional-hardware-input.json').read_text())
todo=[(r['source'],r['ref'],f) for r in inventories for f in r['files']]
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    for n,result in enumerate(pool.map(download,todo),1):
        results.append(result)
        if n%25==0: print(f'{n}/{len(todo)} additional reference files processed',flush=True)
(DEST/'additional-manifest.json').write_text(json.dumps(results,indent=2)+'\n')
failures=[r for r in results if 'error' in r]
print(json.dumps(dict(files=len(results),failed=len(failures),bytes=sum(r.get('bytes',0) for r in results))))
for f in failures: print(f)
if failures: raise SystemExit(1)
