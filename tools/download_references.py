"""Download pinned public Particle reference files and verify Git blob hashes."""
import concurrent.futures
import hashlib
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'references'


def download(item):
    repo,ref,f=item
    relative=Path(repo)/f['path']
    if '..' in relative.parts or relative.is_absolute(): raise ValueError(relative)
    path=DEST/relative
    url=f'https://raw.githubusercontent.com/{repo}/{ref}/'+urllib.parse.quote(f['path'],safe='/')
    last=None
    for attempt in range(3):
        try:
            data=path.read_bytes() if path.exists() else urllib.request.urlopen(url,timeout=60).read()
            blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            if blob!=f['sha']: raise ValueError('Git blob mismatch: '+str(relative))
            path.parent.mkdir(parents=True,exist_ok=True)
            if not path.exists():
                temp=path.with_suffix(path.suffix+'.part')
                temp.write_bytes(data)
                temp.replace(path)
            return dict(path=str(relative),source=url,repository=repo,revision=ref,
                        bytes=len(data),git_blob_sha1=blob,sha256=hashlib.sha256(data).hexdigest())
        except Exception as e:
            last=e
            time.sleep(attempt+1)
    return dict(path=str(relative),source=url,error=str(last))


def main():
    inventories=[json.loads((ROOT/'analysis/schematic-input.json').read_text())]
    inventories+=json.loads((ROOT/'analysis/hardware-schematic-input.json').read_text())
    todo=[(r['source'],r['ref'],f) for r in inventories for f in r.get('files',[])]
    DEST.mkdir(exist_ok=True)
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for n,result in enumerate(pool.map(download,todo),1):
            results.append(result)
            if n%50==0: print(f'{n}/{len(todo)} reference files processed',flush=True)
    results.sort(key=lambda r:r['path'])
    (DEST/'manifest.json').write_text(json.dumps(results,indent=2)+'\n')
    failures=[r for r in results if 'error' in r]
    print(json.dumps(dict(files=len(results),failed=len(failures),bytes=sum(r.get('bytes',0) for r in results))))
    for f in failures: print(f)
    if failures: raise SystemExit(1)


if __name__=='__main__': main()
