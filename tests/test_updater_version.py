"""Exercise the hash-pinned package's actual version reader, never its flash entry point."""
import json
import os
import re
import subprocess
from pathlib import Path

import pytest

from build_physical_firmware import ROOT, build
from fetch_firmware import verify
from inventory import load_image


@pytest.fixture(scope='module')
def packaged_reader():
    manifest = json.loads((ROOT / 'references/firmware-manifest.json').read_text())
    entry = next(item for item in manifest['files'] if item['member'] == 'usr/bin/particle-tachyon-syscon.sh')
    data = (ROOT / entry['path']).read_bytes()
    verify(data, entry)
    function = re.search(r'^read_local_version\(\) \{\n.*?^\}', data.decode(), re.M | re.S)
    assert function, 'Pinned package no longer exposes the audited version-reader function'
    # Extract only the reader. Sourcing the whole updater could run its command
    # dispatcher; these tests must never execute GPIO, UART or flashing code.
    script = function[0] + '\nread_local_version\n'

    def read(image):
        return subprocess.run(['bash', '-c', script], env={**os.environ, 'SYSCON_BIN': str(image)},
                              text=True, capture_output=True, timeout=10)
    return read


@pytest.fixture(scope='module')
def physical(tmp_path_factory):
    output = tmp_path_factory.mktemp('updater-version')
    manifest = build(output)
    assert manifest['status'] == 'linked-experimental'
    assert manifest['inputs_unchanged_during_build']
    assert not manifest['layout_audit']['issues']
    return (output / 'firmware.bin').read_bytes(), manifest['layout_audit']['symbols']['syscon_firmware_version']


def test_packaged_reader_accepts_original_and_rebuilt_firmware(packaged_reader, physical, tmp_path):
    candidate, version_address = physical
    for name, data in [('original', load_image()), ('rebuilt', candidate)]:
        image = tmp_path / (name + '.bin')
        image.write_bytes(data)
        expected = data[version_address:].split(b'\0', 1)[0].decode()
        assert expected
        result = packaged_reader(image)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == expected


@pytest.mark.parametrize('version', [b'0.0.1', b'9.9.99'])
def test_version_reader_accepts_edited_version_text(packaged_reader, physical, tmp_path, version):
    data, address = physical
    image = tmp_path / 'edited-version.bin'
    image.write_bytes(data[:address] + version + b'\0')
    result = packaged_reader(image)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().encode() == version


def test_reader_rejects_erased_padding_without_separator(packaged_reader, physical, tmp_path):
    data, address = physical
    broken = bytearray(data)
    assert broken[address - 1] == 0
    broken[address - 1] = 0xff
    image = tmp_path / 'missing-separator.bin'
    image.write_bytes(broken)
    result = packaged_reader(image)
    assert result.returncode != 0
    assert 'UnicodeDecodeError' in result.stderr
