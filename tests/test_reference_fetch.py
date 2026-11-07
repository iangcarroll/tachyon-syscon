"""Pinned reference hydration, cache validation and rejected partial downloads."""
import copy
import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest
import fetch_references as fetcher


def digest(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def write_manifest(path, entries):
    path.write_text(json.dumps({'schema_version': 1, 'entries': entries}))
    return path


@pytest.fixture
def payloads(tmp_path, monkeypatch):
    raw = b'header contents\n'
    member = b'<device>test register metadata</device>'
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, 'w') as stream:
        stream.writestr('03_SVD/device.svd', member)
    packed = archive.getvalue()
    entries = [
        dict(path='ti/header.h', url='https://example.test/header', group='test-ti',
             **digest(raw + b'\n'), download=digest(raw), transform='append-lf'),
        dict(path='ti/device.pack', url='https://example.test/pack', group='test-ti',
             **digest(packed), extract=[dict(member='03_SVD/device.svd', path='ti/device.svd', **digest(member))]),
        dict(path='hardware/board.zip', url='https://example.test/cad', group='hardware-other', **digest(b'CAD')),
    ]
    bodies = {entries[0]['url']: raw, entries[1]['url']: packed, entries[2]['url']: b'CAD'}
    requests = []
    def urlopen(request, timeout):
        assert timeout > 0
        requests.append(request.full_url)
        return io.BytesIO(bodies[request.full_url])
    monkeypatch.setattr(fetcher.urllib.request, 'urlopen', urlopen)
    manifest = write_manifest(tmp_path/'manifest.json', entries)
    return dict(entries=entries, bodies=bodies, requests=requests, manifest=manifest,
                root=tmp_path/'new-root', member=member)


def test_clean_hydration_default_group_cached_replay_and_opt_in(payloads):
    p = payloads
    result = fetcher.fetch(p['manifest'], p['root'])
    assert result == dict(cached=0, downloaded=2, bytes_downloaded=sum(len(p['bodies'][url]) for url in p['requests']))
    assert (p['root']/'ti/header.h').read_bytes() == p['bodies'][p['entries'][0]['url']] + b'\n'
    assert (p['root']/'ti/device.svd').read_bytes() == p['member']
    assert not (p['root']/'hardware').exists()
    p['requests'].clear()
    assert fetcher.fetch(p['manifest'], p['root']) == dict(cached=2, downloaded=0, bytes_downloaded=0)
    assert p['requests'] == []
    result = fetcher.fetch(p['manifest'], p['root'], groups=['hardware-other'])
    assert result['downloaded'] == 1
    assert (p['root']/'hardware/board.zip').read_bytes() == b'CAD'
    assert p['requests'] == ['https://example.test/cad']


def test_check_is_read_only_and_rejects_modified_extraction(payloads, monkeypatch):
    p = payloads
    fetcher.fetch(p['manifest'], p['root'])
    p['requests'].clear()
    def no_write(*args, **kwargs):
        raise AssertionError('check mode attempted a write')
    monkeypatch.setattr(fetcher, 'atomic_write', no_write)
    assert fetcher.fetch(p['manifest'], p['root'], check=True)['cached'] == 2
    extracted = p['root']/'ti/device.svd'
    extracted.write_bytes(b'tampered')
    with pytest.raises(ValueError, match='corrupt cached'):
        fetcher.fetch(p['manifest'], p['root'], check=True)
    assert extracted.read_bytes() == b'tampered'
    extracted.unlink()
    with pytest.raises(ValueError, match='Missing or corrupt'):
        fetcher.fetch(p['manifest'], p['root'], check=True)
    assert not extracted.exists() and p['requests'] == []


def test_check_missing_cache_does_not_create_destination_or_download(payloads):
    p = payloads
    with pytest.raises(ValueError, match='Missing cached'):
        fetcher.fetch(p['manifest'], p['root'], check=True)
    assert not p['root'].exists() and not p['requests']


def test_fetch_repairs_extracted_file_from_verified_cached_pack(payloads):
    p = payloads
    fetcher.fetch(p['manifest'], p['root'])
    (p['root']/'ti/device.svd').write_bytes(b'tampered')
    p['requests'].clear()
    assert fetcher.fetch(p['manifest'], p['root'])['downloaded'] == 0
    assert (p['root']/'ti/device.svd').read_bytes() == p['member']
    assert p['requests'] == []


@pytest.mark.parametrize('kind', ['same-size-corruption', 'truncated', 'oversized'])
def test_bad_network_bytes_never_publish(payloads, kind):
    p = payloads;url = p['entries'][0]['url'];raw = p['bodies'][url]
    p['bodies'][url] = {'same-size-corruption': b'X'+raw[1:], 'truncated': raw[:-1], 'oversized': raw+b'X'}[kind]
    with pytest.raises(ValueError, match='mismatch'):
        fetcher.fetch(p['manifest'], p['root'])
    assert not p['root'].exists()


@pytest.mark.parametrize('check', [False, True])
def test_corrupt_cached_download_is_not_replaced_or_accepted(payloads, check):
    p = payloads;fetcher.fetch(p['manifest'], p['root']);p['requests'].clear()
    path = p['root']/'ti/device.pack';path.write_bytes(b'bad cache')
    with pytest.raises(ValueError, match='mismatch'):
        fetcher.fetch(p['manifest'], p['root'], check=check)
    assert path.read_bytes() == b'bad cache' and not p['requests']


@pytest.mark.parametrize('mutation', ['digest', 'length', 'missing', 'duplicated'])
def test_bad_archive_member_does_not_publish_archive_or_members(payloads, mutation):
    p = payloads;entry = copy.deepcopy(p['entries'][1]);body = p['bodies'][entry['url']]
    if mutation == 'digest':entry['extract'][0]['sha256'] = '0'*64
    elif mutation == 'length':entry['extract'][0]['bytes'] += 1
    elif mutation == 'missing':entry['extract'][0]['member'] = '03_SVD/missing.svd'
    else:
        archive = io.BytesIO()
        with zipfile.ZipFile(archive, 'w') as stream:
            stream.writestr('03_SVD/device.svd', p['member'])
            with pytest.warns(UserWarning, match='Duplicate name'):
                stream.writestr('03_SVD/device.svd', p['member'])
        body = archive.getvalue();entry.update(digest(body));p['bodies'][entry['url']] = body
    write_manifest(p['manifest'], [entry])
    with pytest.raises(ValueError):fetcher.fetch(p['manifest'], p['root'])
    assert not p['root'].exists()


@pytest.mark.parametrize('field,value', [
    ('path', '../escape'), ('path', '/absolute'), ('path', 'a/../b'), ('path', 'a//b'),
    ('path', 'a\\b'), ('path', ''), ('path', None), ('bytes', -1), ('bytes', True),
    ('sha256', 'not-a-hash'), ('group', 'typo'), ('url', 'http://example.test/file'),
    ('url', 'https://user:password@example.test/file'), ('transform', 'strip-newlines'),
    ('extract', {}), ('download', {}),
])
def test_invalid_entry_rejected_before_network(payloads, field, value):
    p = payloads;entries = copy.deepcopy(p['entries']);entries[0][field] = value
    write_manifest(p['manifest'], entries)
    with pytest.raises(ValueError):fetcher.fetch(p['manifest'], p['root'])
    assert p['requests'] == [] and not p['root'].exists()


def test_schema_duplicate_paths_and_transform_contract_validation(payloads):
    entries = payloads['entries']
    for document in [None, {}, {'schema_version': True, 'entries': entries},
                     {'schema_version': 2, 'entries': entries}, {'schema_version': 1, 'entries': []}]:
        with pytest.raises(ValueError):fetcher.validate_manifest(document)
    changes = []
    duplicate = copy.deepcopy(entries);duplicate.append(copy.deepcopy(entries[0]));changes.append(duplicate)
    conflict = copy.deepcopy(entries);conflict[2]['path'] = 'ti';changes.append(conflict)
    unbound = copy.deepcopy(entries);del unbound[0]['download'];changes.append(unbound)
    wrong_length = copy.deepcopy(entries);wrong_length[0]['bytes'] += 1;changes.append(wrong_length)
    hidden_transform = copy.deepcopy(entries);del hidden_transform[0]['transform'];changes.append(hidden_transform)
    member_escape = copy.deepcopy(entries);member_escape[1]['extract'][0]['member'] = '../escape';changes.append(member_escape)
    member_duplicate = copy.deepcopy(entries);member_duplicate[1]['extract'] *= 2;changes.append(member_duplicate)
    for changed in changes:
        with pytest.raises(ValueError):fetcher.validate_manifest({'schema_version': 1, 'entries': changed})


def test_symlink_escape_and_unknown_group_rejected_before_fetch(payloads, tmp_path):
    p = payloads;p['root'].mkdir();outside = tmp_path/'outside';outside.mkdir()
    (p['root']/'ti').symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match='escapes'):fetcher.fetch(p['manifest'], p['root'])
    for groups in [[], ['typo'], ['hardware-tachyon']]:
        with pytest.raises(ValueError):fetcher.fetch(p['manifest'], p['root'], groups=groups)
    assert p['requests'] == [] and list(outside.iterdir()) == []


def test_cli_defaults_are_repository_relative_and_check_is_forwarded(monkeypatch, tmp_path, capsys):
    calls = []
    def fake_fetch(*args, **kwargs):
        calls.append((args, kwargs));return {'verified': True}
    monkeypatch.setattr(fetcher, 'fetch', fake_fetch);monkeypatch.chdir(tmp_path)
    fetcher.main(['--check'])
    assert calls == [((fetcher.ROOT/'references/fetch-manifest.json', fetcher.ROOT/'references', ('test-ti',)), {'check': True})]
    assert json.loads(capsys.readouterr().out) == {'verified': True}


def test_repository_manifest_keeps_ti_pins_and_optional_hardware_separate():
    entries = fetcher.validate_manifest(json.loads(fetcher.DEFAULT_MANIFEST.read_text()))
    core = {entry['path']: entry for entry in entries if entry['group'] == 'test-ti'}
    retained = json.loads((fetcher.ROOT/'references/ti-mspm0/manifest.json').read_text())
    for item in retained:
        entry = core['ti-mspm0/'+item['path']]
        assert entry['sha256'] == item['sha256'] and entry['url'] == item['source_url']
        assert entry['transform'] == 'append-lf'
    pack = json.loads((fetcher.ROOT/'references/ti-mspm0/pack-manifest.json').read_text())
    entry = core['ti-mspm0/'+Path(pack['url']).name]
    assert entry['sha256'] == pack['sha256'] and entry['bytes'] == pack['bytes']
    assert {member['member'] for member in entry['extract']} == set(pack['extracted'])
    assert all(entry['group'].startswith('hardware-') for entry in entries if not entry['path'].startswith('ti-mspm0/'))
