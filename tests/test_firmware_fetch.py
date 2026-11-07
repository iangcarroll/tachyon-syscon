"""Archive pipeline tests use synthetic payloads; live verification is opt-in."""
import copy
import hashlib
import io
import json
import lzma
import os
from pathlib import Path
import tarfile
import pytest
import fetch_firmware as ff


def digest(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def ar(entries):
    result = b'!<arch>\n'
    for name, data in entries:
        header = (f'{name}/'.ljust(16) + '0'.ljust(12) + '0'.ljust(6) +
                  '0'.ljust(6) + '100644'.ljust(8) + str(len(data)).ljust(10) + '`\n')
        result += header.encode('ascii') + data + (b'\n' if len(data) % 2 else b'')
    return result


def package(contents, extra=()):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for name, data in contents.items():
            member = tarfile.TarInfo('./' + name)
            member.size = len(data)
            archive.addfile(member, io.BytesIO(data))
        for member in extra:
            archive.addfile(member)
    raw = stream.getvalue()
    compressed = lzma.compress(raw)
    blob = ar([('debian-binary', b'2.0\n'), ('control.tar.xz', b'unexecuted'), ('data.tar.xz', compressed)])
    return blob, compressed, raw


@pytest.fixture
def bundle(tmp_path):
    contents = {'usr/lib/firmware/reference.bin': b'firmware\x00\x12\x34',
                'usr/lib/firmware/reference.hex': b':00000001FF\n',
                'usr/bin/mspm0flash': b'not executable test data'}
    blob, compressed, raw = package(contents)
    paths = ['firmware/reference.bin', 'firmware/reference.hex', 'build/reference-tools/mspm0flash']
    doc = {'schema_version': 1,
           'package': {'url': 'https://packages.particle.io/debian/pool/test/reference.deb', **digest(blob)},
           'data_archive': {'member': 'data.tar.xz', **digest(compressed), 'uncompressed_bytes': len(raw)},
           'files': [{'member': name, 'path': path, 'role': 'updater' if '/bin/' in name else 'firmware', **digest(data)}
                     for (name, data), path in zip(contents.items(), paths)]}
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps(doc))
    return {'contents': contents, 'blob': blob, 'doc': doc, 'manifest': manifest, 'root': tmp_path / 'output'}


def repackage(bundle, contents=None, extra=()):
    blob, compressed, raw = package(contents or bundle['contents'], extra)
    doc = copy.deepcopy(bundle['doc'])
    doc['package'].update(digest(blob))
    doc['data_archive'].update(digest(compressed), uncompressed_bytes=len(raw))
    return blob, doc


def test_fetch_check_cache_repair_and_optional_updater_pipeline(bundle, monkeypatch):
    calls = []
    def download(entry):
        calls.append(entry['url'])
        return bundle['blob']
    monkeypatch.setattr(ff, 'download', download)
    first = ff.fetch(bundle['manifest'], bundle['root'])
    assert first['downloaded'] and len(calls) == 1
    for entry in bundle['doc']['files'][:2]:
        assert (bundle['root'] / entry['path']).read_bytes() == bundle['contents'][entry['member']]
    updater = bundle['root'] / bundle['doc']['files'][2]['path']
    assert not updater.exists()
    first_path = bundle['root'] / bundle['doc']['files'][0]['path']
    mtime = first_path.stat().st_mtime_ns
    assert not ff.fetch(bundle['manifest'], bundle['root'], check=True)['downloaded']
    assert not ff.fetch(bundle['manifest'], bundle['root'])['downloaded']
    assert len(calls) == 1 and first_path.stat().st_mtime_ns == mtime
    first_path.write_bytes(b'broken')
    with pytest.raises(ValueError, match='Missing or corrupt'):
        ff.fetch(bundle['manifest'], bundle['root'], check=True)
    assert len(calls) == 1
    ff.fetch(bundle['manifest'], bundle['root'], with_updater=True)
    assert len(calls) == 2 and updater.read_bytes() == bundle['contents']['usr/bin/mspm0flash']
    assert first_path.read_bytes() == bundle['contents'][bundle['doc']['files'][0]['member']]


def test_check_missing_cache_has_no_network_or_writes(bundle, monkeypatch):
    def forbidden(*args):
        pytest.fail('check mode performed network or writes')
    monkeypatch.setattr(ff, 'download', forbidden)
    monkeypatch.setattr(ff, 'atomic_write', forbidden)
    with pytest.raises(ValueError, match='Missing or corrupt'):
        ff.fetch(bundle['manifest'], bundle['root'], check=True)
    assert not bundle['root'].exists()


@pytest.mark.parametrize('mutation', ['package_digest', 'data_digest', 'payload_digest', 'payload_missing'])
def test_corrupt_pipeline_never_publishes_partial_payloads(bundle, monkeypatch, mutation):
    doc, blob = copy.deepcopy(bundle['doc']), bundle['blob']
    if mutation == 'package_digest':
        blob = blob[:-1] + bytes([blob[-1] ^ 1])
    elif mutation == 'data_digest':
        doc['data_archive']['sha256'] = '0' * 64
    elif mutation == 'payload_digest':
        doc['files'][1]['sha256'] = '0' * 64
    else:
        contents = dict(bundle['contents'])
        del contents['usr/lib/firmware/reference.hex']
        blob, doc = repackage(bundle, contents)
    bundle['manifest'].write_text(json.dumps(doc))
    monkeypatch.setattr(ff, 'download', lambda entry: blob)
    with pytest.raises(ValueError):
        ff.fetch(bundle['manifest'], bundle['root'], with_updater=True)
    assert not bundle['root'].exists()


@pytest.mark.parametrize('kind', ['symlink', 'hardlink', 'device', 'traversal', 'absolute', 'duplicate', 'directory_payload'])
def test_reject_unsafe_tar_members_even_when_not_selected(bundle, kind):
    member = tarfile.TarInfo('extra')
    if kind in ('symlink', 'hardlink'):
        member.type = tarfile.SYMTYPE if kind == 'symlink' else tarfile.LNKTYPE
        member.linkname = '/etc/passwd'
    elif kind == 'device':
        member.type = tarfile.CHRTYPE
    elif kind == 'traversal':
        member.name = '../outside'
    elif kind == 'absolute':
        member.name = '/outside'
    elif kind == 'duplicate':
        member.name = './usr/lib/firmware/reference.bin'
    else:
        member.name = './usr/lib/firmware/reference.bin'
        member.type = tarfile.DIRTYPE
    blob, doc = repackage(bundle, extra=[member])
    with pytest.raises(ValueError):
        ff.payloads(blob, doc)


@pytest.mark.parametrize('mutation', ['magic', 'truncated', 'duplicate', 'unknown', 'version'])
def test_ar_structure_rejected(mutation):
    entries = [('debian-binary', b'2.0\n'), ('control.tar.xz', b'control'), ('data.tar.xz', b'data')]
    if mutation == 'duplicate':
        entries.append(entries[-1])
    elif mutation == 'unknown':
        entries.append(('other', b'x'))
    elif mutation == 'version':
        entries[0] = ('debian-binary', b'3.0\n')
    blob = ar(entries)
    if mutation == 'magic':
        blob = b'wrong' + blob[5:]
    elif mutation == 'truncated':
        blob = blob[:-1]
    with pytest.raises(ValueError):
        ff.ar_members(blob)


def test_decompression_bound_is_enforced(bundle):
    doc = copy.deepcopy(bundle['doc'])
    doc['data_archive']['uncompressed_bytes'] -= 1
    with pytest.raises(ValueError, match='bound'):
        ff.payloads(bundle['blob'], doc)


@pytest.mark.parametrize('field,value', [('path','../escape'), ('path','/absolute'), ('member','a/../b'), ('role','unknown')])
def test_manifest_rejects_invalid_payload(bundle, field, value):
    doc = copy.deepcopy(bundle['doc'])
    doc['files'][0][field] = value
    with pytest.raises(ValueError):
        ff.validate_manifest(doc)


@pytest.mark.parametrize('url', ['http://packages.particle.io/debian/pool/x', 'https://other.example/debian/pool/x',
                               'https://user:password@packages.particle.io/debian/pool/x'])
def test_source_url_restrictions(url):
    with pytest.raises(ValueError):
        ff.official_url(url)


@pytest.mark.parametrize('parent', [False, True])
def test_cached_destination_symlink_is_rejected(bundle, monkeypatch, tmp_path, parent):
    bundle['root'].mkdir()
    outside = tmp_path / 'outside'
    outside.mkdir()
    if parent:
        (bundle['root'] / 'firmware').symlink_to(outside, target_is_directory=True)
    else:
        (bundle['root'] / 'firmware').mkdir()
        target = outside / 'file'
        target.write_bytes(bundle['contents']['usr/lib/firmware/reference.bin'])
        (bundle['root'] / 'firmware/reference.bin').symlink_to(target)
    monkeypatch.setattr(ff, 'download', lambda entry: pytest.fail('unsafe destination reached download'))
    with pytest.raises(ValueError, match='Symlink'):
        ff.fetch(bundle['manifest'], bundle['root'])


def test_cli_check_emits_json_without_fetch(bundle, monkeypatch, capsys):
    monkeypatch.setattr(ff, 'download', lambda entry: bundle['blob'])
    ff.fetch(bundle['manifest'], bundle['root'])
    monkeypatch.setattr(ff, 'download', lambda entry: pytest.fail('check downloaded'))
    assert ff.main(['--manifest', str(bundle['manifest']), '--root', str(bundle['root']), '--check']) == 0
    result = json.loads(capsys.readouterr().out)
    assert result['check_only'] and not result['downloaded']


def test_atomic_write_failure_keeps_previous_file_and_cleans_temporary(tmp_path, monkeypatch):
    target = tmp_path / 'file'
    target.write_bytes(b'old')
    def fail(*args):
        raise OSError('simulated failed publication')
    monkeypatch.setattr(os, 'replace', fail)
    with pytest.raises(OSError):
        ff.atomic_write(target, b'new')
    assert target.read_bytes() == b'old' and list(tmp_path.iterdir()) == [target]


@pytest.mark.skipif(os.environ.get('SYSCON_FETCH_NETWORK') != '1', reason='set SYSCON_FETCH_NETWORK=1 for pinned official download')
def test_fresh_official_package_matches_reference_and_offline_cache(tmp_path, monkeypatch):
    result = ff.fetch(root=tmp_path, with_updater=True)
    assert result['downloaded']
    doc = json.loads(ff.DEFAULT_MANIFEST.read_text())
    for entry in doc['files']:
        contents = (tmp_path / entry['path']).read_bytes()
        ff.verify(contents, entry)
        original = ff.ROOT / entry['path']
        if original.is_file():
            assert original.read_bytes() == contents
    monkeypatch.setattr(ff, 'download', lambda entry: pytest.fail('check downloaded'))
    assert not ff.fetch(root=tmp_path, check=True, with_updater=True)['downloaded']


def test_same_size_cache_corruption_is_detected_without_writes(bundle, monkeypatch):
    monkeypatch.setattr(ff, 'download', lambda entry: bundle['blob'])
    ff.fetch(bundle['manifest'], bundle['root'])
    path = bundle['root'] / bundle['doc']['files'][0]['path']
    changed = bytearray(path.read_bytes())
    changed[-1] ^= 1
    path.write_bytes(changed)
    mtime = path.stat().st_mtime_ns
    monkeypatch.setattr(ff, 'download', lambda entry: pytest.fail('check downloaded'))
    with pytest.raises(ValueError, match='Missing or corrupt'):
        ff.fetch(bundle['manifest'], bundle['root'], check=True)
    assert path.read_bytes() == changed and path.stat().st_mtime_ns == mtime


@pytest.mark.parametrize('mutation', ['duplicate_member', 'duplicate_destination', 'file_directory_conflict'])
def test_manifest_rejects_ambiguous_payloads(bundle, mutation):
    doc = copy.deepcopy(bundle['doc'])
    if mutation == 'duplicate_member':
        doc['files'][1]['member'] = doc['files'][0]['member']
    elif mutation == 'duplicate_destination':
        doc['files'][1]['path'] = doc['files'][0]['path']
    else:
        doc['files'][1]['path'] = doc['files'][0]['path'] + '/child'
    with pytest.raises(ValueError):
        ff.validate_manifest(doc)
