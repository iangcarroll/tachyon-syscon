"""Fetch pinned reference firmware without installing or executing its package.

Only verified regular-file payloads are written. The optional updater is a local
reference for offline audit; this tool does not execute it or access any device.
"""
import argparse
import hashlib
import io
import json
import lzma
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile
import tempfile
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / 'references/firmware-manifest.json'


def safe_relative(value):
    if (not isinstance(value, str) or not value or '\\' in value or '\x00' in value
            or PurePosixPath(value).is_absolute()
            or any(part in ('', '.', '..') for part in value.split('/'))):
        raise ValueError('Expected a safe relative path')
    return value


def digest_fields(entry, limit):
    if (not isinstance(entry, dict) or type(entry.get('bytes')) is not int
            or not 0 < entry['bytes'] <= limit
            or not isinstance(entry.get('sha256'), str)
            or not re.fullmatch('[0-9a-f]{64}', entry['sha256'])):
        raise ValueError('Invalid pinned size or SHA256')


def official_url(url):
    if not isinstance(url, str):
        raise ValueError('Expected official HTTPS package URL')
    p = urllib.parse.urlsplit(url)
    if (p.scheme != 'https' or p.netloc != 'packages.particle.io'
            or p.fragment or p.query or not p.path.startswith('/debian/pool/')):
        raise ValueError('Expected official HTTPS package URL')
    return url


def validate_manifest(doc):
    if not isinstance(doc, dict) or type(doc.get('schema_version')) is not int or doc['schema_version'] != 1:
        raise ValueError('Unsupported firmware manifest schema')
    package = doc.get('package')
    digest_fields(package, 2 * 1024 * 1024)
    official_url(package.get('url'))
    archive = doc.get('data_archive')
    digest_fields(archive, package['bytes'])
    if archive.get('member') != 'data.tar.xz':
        raise ValueError('Expected pinned data.tar.xz member')
    if type(archive.get('uncompressed_bytes')) is not int or not 0 < archive['uncompressed_bytes'] <= 16 * 1024 * 1024:
        raise ValueError('Invalid uncompressed archive bound')
    files = doc.get('files')
    if not isinstance(files, list) or not files:
        raise ValueError('Expected firmware payload entries')
    members, paths = set(), set()
    for entry in files:
        digest_fields(entry, archive['uncompressed_bytes'])
        member, path = safe_relative(entry.get('member')), safe_relative(entry.get('path'))
        if entry.get('role') not in ('firmware', 'updater'):
            raise ValueError('Unknown payload role')
        if member in members or path in paths:
            raise ValueError('Duplicate payload member or destination')
        members.add(member)
        paths.add(path)
    if not any(e['role'] == 'firmware' for e in files):
        raise ValueError('No firmware payload selected')
    for path in paths:
        if any(str(parent) in paths for parent in PurePosixPath(path).parents):
            raise ValueError('Payload file/directory conflict')
    return doc


def verify(data, entry):
    if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise ValueError('Pinned size or SHA256 mismatch: ' + entry.get('path', entry.get('member', 'package')))


def destination(root, relative):
    path = root
    for part in safe_relative(relative).split('/'):
        path = path / part
        if path.is_symlink():
            raise ValueError('Symlink in destination path: ' + relative)
    if path.exists() and not stat.S_ISREG(path.stat().st_mode):
        raise ValueError('Destination is not a regular file: ' + relative)
    return path


def cached(path, entry):
    if not path.exists():
        return False
    if path.stat().st_size != entry['bytes']:
        return False
    return hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256']


def download(package):
    # A redirect is checked before reading its response body as well.
    class OfficialRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            official_url(newurl)
            return super().redirect_request(request, fp, code, msg, headers, newurl)
    opener = urllib.request.build_opener(OfficialRedirect())
    with opener.open(official_url(package['url']), timeout=60) as response:
        official_url(response.geturl())
        data = response.read(package['bytes'] + 1)
    verify(data, package)
    return data


def ar_members(data):
    """Parse the three simple ar members used by this pinned Debian package."""
    if not data.startswith(b'!<arch>\n'):
        raise ValueError('Invalid ar magic')
    offset, members = 8, {}
    while offset < len(data):
        header = data[offset:offset + 60]
        if len(header) != 60 or header[58:60] != b'`\n':
            raise ValueError('Truncated or malformed ar header')
        try:
            name = header[:16].decode('ascii').strip().removesuffix('/')
            size_text = header[48:58].decode('ascii').strip()
            if not size_text.isdecimal():
                raise ValueError('Invalid ar member size')
            size = int(size_text)
        except UnicodeDecodeError as exc:
            raise ValueError('Invalid ar header encoding') from exc
        if name not in ('debian-binary', 'control.tar.xz', 'data.tar.xz') or name in members:
            raise ValueError('Unexpected or duplicate ar member')
        begin, end = offset + 60, offset + 60 + size
        if end + size % 2 > len(data):
            raise ValueError('Truncated ar member')
        if size % 2 and data[end:end + 1] != b'\n':
            raise ValueError('Invalid ar padding')
        members[name] = data[begin:end]
        offset = end + size % 2
    if set(members) != {'debian-binary', 'control.tar.xz', 'data.tar.xz'} or members['debian-binary'] != b'2.0\n':
        raise ValueError('Unexpected Debian archive structure')
    return members


def payloads(data, manifest):
    verify(data, manifest['package'])
    compressed = ar_members(data)[manifest['data_archive']['member']]
    verify(compressed, manifest['data_archive'])
    decoder = lzma.LZMADecompressor(memlimit=64 * 1024 * 1024)
    raw = decoder.decompress(compressed, max_length=manifest['data_archive']['uncompressed_bytes'] + 1)
    if len(raw) != manifest['data_archive']['uncompressed_bytes'] or not decoder.eof or decoder.unused_data:
        raise ValueError('Compressed data archive violates pinned bound')
    wanted = {entry['member']: entry for entry in manifest['files']}
    found, seen = {}, set()
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        for member in archive:
            name = member.name
            if name.startswith('./'):
                name = name[2:]
            if name == '.':
                if not member.isdir():
                    raise ValueError('Invalid archive root')
                continue
            safe_relative(name)
            if name in seen:
                raise ValueError('Duplicate tar member')
            seen.add(name)
            if not (member.isdir() or member.isfile()) or member.issparse() or member.pax_headers:
                raise ValueError('Unsupported tar member type or metadata')
            if member.isdir():
                if member.size != 0 or name in wanted:
                    raise ValueError('Invalid directory payload')
                continue
            if member.size < 0 or member.offset_data + member.size > len(raw):
                raise ValueError('Tar member exceeds archive bounds')
            if name in wanted:
                entry = wanted[name]
                if member.size != entry['bytes']:
                    raise ValueError('Pinned payload size mismatch')
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError('Missing regular payload stream')
                contents = stream.read(entry['bytes'] + 1)
                verify(contents, entry)
                found[name] = contents
    if found.keys() != wanted.keys():
        raise ValueError('Required firmware payload missing')
    return found


def atomic_write(path, contents):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def fetch(manifest=DEFAULT_MANIFEST, root=ROOT, check=False, with_updater=False):
    doc = validate_manifest(json.loads(Path(manifest).read_text()))
    root = Path(root).resolve()
    selected = [e for e in doc['files'] if e['role'] == 'firmware' or with_updater]
    paths = [(e, destination(root, e['path'])) for e in selected]
    missing = [(e, p) for e, p in paths if not cached(p, e)]
    if missing and check:
        raise ValueError('Missing or corrupt cached payload: ' + ', '.join(e['path'] for e, _ in missing))
    if missing:
        contents = payloads(download(doc['package']), doc)
        # All archive members and target paths were checked before the first write.
        for entry, path in missing:
            destination(root, entry['path'])
            atomic_write(path, contents[entry['member']])
    return {'verified': [e['path'] for e in selected], 'downloaded': bool(missing), 'check_only': check}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--root', type=Path, default=ROOT, help='root for manifest-relative output paths')
    parser.add_argument('--check', action='store_true', help='verify cached selected payloads without network or writes')
    parser.add_argument('--with-updater', action='store_true', help='also cache the updater for offline inspection; never execute it')
    args = parser.parse_args(argv)
    try:
        result = fetch(args.manifest, args.root, args.check, args.with_updater)
    except (ValueError, OSError, EOFError, lzma.LZMAError, tarfile.TarError) as exc:
        parser.exit(1, f'Firmware fetch failed: {exc}\n')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
