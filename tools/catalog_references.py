"""Verify every download and produce a searchable local reference catalog."""
import collections
import hashlib
import html
import json
import urllib.parse
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'references'

def main():
    entries={}
    for name in ('manifest.json','additional-manifest.json','web-manifest.json'):
        for entry in json.loads((ROOT/name).read_text()):
            if 'error' in entry: raise ValueError(entry)
            entries[entry['path']]=entry
    archives={}
    for relative,entry in entries.items():
        path=ROOT/relative
        data=path.read_bytes()
        assert len(data)==entry['bytes'],relative
        assert hashlib.sha256(data).hexdigest()==entry['sha256'],relative
        if 'git_blob_sha1' in entry:
            assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==entry['git_blob_sha1'],relative
        if path.suffix.lower()=='.zip':
            with zipfile.ZipFile(path) as z:
                assert z.testzip() is None,relative
                archives[relative]=z.namelist()
    rows=sorted(entries.values(),key=lambda e:e['path'])
    (ROOT/'all-manifest.json').write_text(json.dumps(rows,indent=2)+'\n')
    (ROOT/'archive-contents.json').write_text(json.dumps(archives,indent=2)+'\n')
    groups=collections.defaultdict(list)
    for entry in rows: groups[entry.get('repository','developer.particle.io')].append(entry)
    size=sum(e['bytes'] for e in rows)
    out=['# Particle hardware references','',f'Collected 2026-11-07: {len(rows)} verified files, {size:,} bytes.','',
         'Public schematic images, editable CAD, board layouts, design archives, and supporting datasheets from Particle documentation and hardware repositories. Repository assets are pinned to the recorded revisions. This is a snapshot of discovered public sources, not a claim to include unpublished designs or every historical commit.','',
         '## Tachyon','',
         '- [Debug board schematic](developer.particle.io/tachyon/debug-adapter-schematic.png)',
         '- [Source page snapshot](developer.particle.io/tachyon/debug-board.html)',
         '- [Tachyon datasheet source](particle-iot/docs/src/content/reference/datasheets/tachyon/tachyon-datasheet.md)',
         '',
         'No mainboard schematic was found in the examined public Tachyon documentation, documentation asset tree, or hardware-library tree. The debug-board schematic describes the adapter, not the full Tachyon power circuitry. Other Particle products are comparison references and do not establish Tachyon pin mappings.','',
         '## Integrity and reproduction','',
         '`all-manifest.json` records source URLs, revisions where available, sizes, and SHA-256 hashes. GitHub files additionally have verified Git blob SHA-1 hashes. `archive-contents.json` lists ZIP members; every archive passed a complete CRC check. Archives are retained intact.','',
         'Run from the project parent directory:','',
         '```sh','syscon-re/.venv/bin/python syscon-re/tools/download_references.py','syscon-re/.venv/bin/python syscon-re/tools/download_additional_references.py','syscon-re/.venv/bin/python syscon-re/tools/catalog_references.py','```','',
         'The web snapshots have their original URLs in `web-manifest.json`. A legacy docs link to `/assets/files/projects/m2-breakout.zip` was absent from the source tree; the separate `m2-breakout-board` repository is included. Preserve the upstream licenses when reusing design files.','',
         '## Inventory','', '| Source | Files | MiB |','| --- | ---: | ---: |']
    for group,es in sorted(groups.items()): out.append(f'| {group} | {len(es)} | {sum(e["bytes"] for e in es)/1024**2:.1f} |')
    for group,es in sorted(groups.items()):
        out+=['',f'## {group}','']
        for e in es:
            label=e['path'].removeprefix(group+'/')
            out.append(f'- [{label}]({urllib.parse.quote(e["path"],safe="/")})')
    (ROOT/'README.md').write_text('\n'.join(out)+'\n')
    print(json.dumps(dict(files=len(rows),bytes=size,archives_checked=len(archives),sources=len(groups))))

if __name__=='__main__': main()
