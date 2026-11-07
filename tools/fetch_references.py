"""Fetch selected pinned references; the default TI group supports emulator tests."""
import argparse
import hashlib
import io
import json
import os
import re
import tempfile
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / 'references/fetch-manifest.json'
GROUPS = ('test-ti', 'hardware-tachyon', 'hardware-other')


def relative_path(value):
    if (not isinstance(value, str) or not value or '\\' in value or
            '\x00' in value or PurePosixPath(value).is_absolute() or
            any(part in ('', '.', '..') for part in value.split('/'))):
        raise ValueError('Expected a safe relative path')
    return value


def digest_fields(entry):
    if not isinstance(entry, dict):
        raise ValueError('Expected digest object')
    if type(entry.get('bytes')) is not int or entry['bytes'] < 0:
        raise ValueError('Expected nonnegative byte length')
    if not isinstance(entry.get('sha256'), str) or not re.fullmatch('[0-9a-f]{64}', entry['sha256']):
        raise ValueError('Expected SHA256 digest')


def validate_manifest(document):
    if not isinstance(document, dict) or type(document.get('schema_version')) is not int or document['schema_version'] != 1:
        raise ValueError('Unsupported reference manifest schema')
    entries = document.get('entries')
    if not isinstance(entries, list) or not entries:
        raise ValueError('Expected nonempty reference entries')
    outputs = set()
    for entry in entries:
        digest_fields(entry)
        relative_path(entry.get('path'))
        if entry.get('group') not in GROUPS:
            raise ValueError('Unknown reference group')
        url = entry.get('url')
        if not isinstance(url, str):
            raise ValueError('Expected HTTPS source URL')
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
            raise ValueError('Expected HTTPS source URL without credentials or fragment')
        if 'download' in entry:
            digest_fields(entry['download'])
        if 'transform' in entry:
            if entry['transform'] != 'append-lf' or 'download' not in entry:
                raise ValueError('Unsupported or unbound transformation')
            if entry['bytes'] != entry['download']['bytes'] + 1:
                raise ValueError('Transformation byte lengths disagree')
        elif 'download' in entry and any(entry[k] != entry['download'][k] for k in ('bytes', 'sha256')):
            raise ValueError('Untransformed download differs from stored digest')
        members = entry.get('extract', [])
        if not isinstance(members, list):
            raise ValueError('Expected archive member list')
        seen_members = set()
        for member in members:
            digest_fields(member)
            relative_path(member.get('member'))
            relative_path(member.get('path'))
            if member['member'] in seen_members:
                raise ValueError('Duplicate archive member')
            seen_members.add(member['member'])
        for item in [entry, *members]:
            path = item['path']
            if path in outputs:
                raise ValueError('Duplicate reference destination: ' + path)
            outputs.add(path)
    for path in outputs:
        if any(str(parent) in outputs for parent in PurePosixPath(path).parents):
            raise ValueError('Reference file/directory conflict: ' + path)
    return entries


def destination(root, relative):
    relative_path(relative)
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or path == root.resolve():
        raise ValueError('Reference path escapes destination: ' + relative)
    return path


def verify(data, entry):
    label = entry.get('path', entry.get('member', 'download'))
    if len(data) != entry['bytes']:
        raise ValueError('Size mismatch: ' + label)
    if hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise ValueError('SHA256 mismatch: ' + label)


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def install(root, entry, data, check=False):
    verify(data, entry)
    files = [(destination(root, entry['path']), data)]
    # Validate all requested members before publishing this archive or its files.
    if entry.get('extract'):
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            for member in entry['extract']:
                matches = [info for info in archive.infolist() if info.filename == member['member']]
                if len(matches) != 1 or matches[0].is_dir() or matches[0].file_size != member['bytes']:
                    raise ValueError('Archive member missing, duplicated or wrong size: ' + member['member'])
                contents = archive.read(matches[0])
                verify(contents, member)
                files.append((destination(root, member['path']), contents))
    for path, contents in files:
        if not path.exists() or path.read_bytes() != contents:
            if check:
                raise ValueError('Missing or corrupt cached reference: ' + str(path))
            atomic_write(path, contents)


def fetch(manifest=DEFAULT_MANIFEST, root=ROOT / 'references', groups=('test-ti',), check=False):
    entries = validate_manifest(json.loads(Path(manifest).read_text()))
    if not groups or any(group not in GROUPS for group in groups):
        raise ValueError('Unknown or empty group selection')
    selected = [entry for entry in entries if entry['group'] in groups]
    if set(groups) - {entry['group'] for entry in selected}:
        raise ValueError('Selected group absent from manifest')
    root = Path(root)
    # Reject existing escaping symlinks before any download/publication.
    for entry in selected:
        for item in [entry, *entry.get('extract', [])]:
            destination(root, item['path'])
    counts = {'cached': 0, 'downloaded': 0, 'bytes_downloaded': 0}
    for entry in selected:
        path = destination(root, entry['path'])
        if path.exists():
            data = path.read_bytes()
            counts['cached'] += 1
        else:
            if check:
                raise ValueError('Missing cached reference: ' + str(path))
            request = urllib.request.Request(entry['url'], headers={'User-Agent': 'syscon-reference-fetch/1'})
            download = entry.get('download', entry)
            with urllib.request.urlopen(request, timeout=30) as response:
                data = response.read(download['bytes'] + 1)
            verify(data, download)
            counts['downloaded'] += 1
            counts['bytes_downloaded'] += len(data)
            # Historical TI snapshots contain one extra LF; both hashes are pinned.
            if entry.get('transform') == 'append-lf':
                data += b'\n'
        install(root, entry, data, check=check)
    return counts


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--destination', type=Path, default=ROOT / 'references')
    parser.add_argument('--group', action='append', choices=GROUPS)
    parser.add_argument('--check', action='store_true', help='Verify selected cached files without downloading or writing')
    args = parser.parse_args(argv)
    result = fetch(args.manifest, args.destination, args.group or ('test-ti',), check=args.check)
    print(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    main()
