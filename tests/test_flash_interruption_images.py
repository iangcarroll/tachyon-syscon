"""Fresh CPUs recover every distinct flash prefix of append and compaction."""
import json
import os
import tempfile
from pathlib import Path

import pytest

from build_physical_firmware import build
from flash_interruptions import capture, compare_captures, recover, report
from inventory import load_image


@pytest.fixture(scope='module')
def physical(tmp_path_factory):
    output = tmp_path_factory.mktemp('flash-interruption-image')
    manifest = build(output)
    assert manifest['status'] == 'linked-experimental'
    assert manifest['inputs_unchanged_during_build']
    assert not manifest['layout_audit']['issues']
    assert not manifest['endpoint_stubs_included']
    assert not manifest['original_executable_bytes_included']
    return (output / 'firmware.bin').read_bytes(), manifest['layout_audit']


@pytest.mark.parametrize('case', ['append', 'compact'])
def test_flash_interruption_recovery_at_every_atomic_boundary(physical, tmp_path, case):
    candidate, layout = physical
    artifact_root = os.environ.get('SYSCON_SCENARIO_OUTPUT')
    if artifact_root:
        root = Path(artifact_root)
        root.mkdir(parents=True, exist_ok=True)
        tmp_path = Path(tempfile.mkdtemp(prefix=f'flash-{case}-', dir=root))
    summary = dict(passed=False, case=case, completed_groups=[])
    path = tmp_path / 'summary.json'
    path.write_text(json.dumps(summary))
    try:
        original = capture(load_image(), case, 0x20000820, 0x8f88)
        rebuilt = capture(candidate, case, layout['stack_floor_address'], layout['symbols']['syscon_logger_target'])
        compare_captures(original, rebuilt)
        for role, captured in [('original', original), ('rebuilt', rebuilt)]:
            (tmp_path / (role + '-prefixes.json')).write_text(json.dumps(report(captured), indent=2))
        for index, (a, b) in enumerate(zip(original['unique'], rebuilt['unique'])):
            x = recover(a['image'], 0x20000820)
            y = recover(b['image'], layout['stack_floor_address'])
            artifact = dict(boundaries=a['boundaries'], original=x, rebuilt=y)
            (tmp_path / f'recovery-{index}.json').write_text(json.dumps(artifact, indent=2))
            assert x == y, (case, a['boundaries'], [key for key in x if x[key] != y[key]])
            summary['completed_groups'].append(a['boundaries'])
            path.write_text(json.dumps(summary, indent=2))
        covered = sorted(boundary for group in summary['completed_groups'] for boundary in group)
        assert covered == list(range(len(original['snapshots'])))
        summary.update(passed=True, boundary_count=len(covered))
    finally:
        path.write_text(json.dumps(summary, indent=2))
