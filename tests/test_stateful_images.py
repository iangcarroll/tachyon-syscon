"""Seeded multi-input sessions through actual reset, IRQs, main and flash code."""
import json
import os
import tempfile
from pathlib import Path

import pytest

from build_physical_firmware import build
from stateful_replay import generate, replay


@pytest.fixture(scope='module')
def physical_image(tmp_path_factory):
    output = tmp_path_factory.mktemp('stateful-image')
    manifest = build(output)
    assert manifest['status'] == 'linked-experimental'
    assert manifest['inputs_unchanged_during_build']
    assert not manifest['layout_audit']['issues']
    assert not manifest['endpoint_stubs_included']
    assert not manifest['original_executable_bytes_included']
    return output / 'firmware.bin'


@pytest.mark.parametrize('seed', [17, 73])
def test_stateful_whole_images_agree_and_make_independent_progress(physical_image, tmp_path, seed):
    artifact_root = os.environ.get('SYSCON_SCENARIO_OUTPUT')
    if artifact_root:
        root = Path(artifact_root)
        root.mkdir(parents=True, exist_ok=True)
        tmp_path = Path(tempfile.mkdtemp(prefix=f'stateful-{seed}-', dir=root))
    events = generate(seed, rounds=3)
    result = replay(physical_image, events, tmp_path)
    assert result['passed'], result
    assert result['expected_outcomes'] == [True, True]
    assert json.loads((tmp_path / 'events.json').read_text()) == events
    assert json.loads((tmp_path / 'summary.json').read_text()) == result
