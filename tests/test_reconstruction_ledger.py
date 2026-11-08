"""The source index distinguishes build inputs, test mappings and current results."""
import copy
import json
import subprocess
import sys

import pytest

from inventory import EXPECTED, ROOT
from reconstruction_ledger import MAP, build_inventory, checkpoint_status, markdown
from build_physical_firmware import production_sources


def test_inventory_uses_production_sources_and_preserves_model_provenance():
    ledger = build_inventory()
    sources = set(production_sources())
    for row in ledger['functions']:
        mapping = MAP[int(row['address'], 16)]
        assert row['source'] in sources
        assert row['source'] == mapping.get('target_abi', {}).get('source', mapping['source'])
        assert not row['source'].startswith('tests/')
        for test in row['tests']:
            assert (ROOT / test).is_file()
        if mapping['source'].startswith('tests/'):
            assert row['legacy_model'] == mapping['source']
    assert any(row['legacy_model'] for row in ledger['functions'])


def test_promoted_folded_helpers_keep_their_original_model():
    promoted = {
        address: next(path for path in mapping['additional_sources']
                      if path.startswith('tests/models/'))
        for address, mapping in MAP.items()
        if not mapping['source'].startswith('tests/')
        and any(path.startswith('tests/models/')
                for path in mapping.get('additional_sources', []))
    }
    assert promoted
    for row in build_inventory()['functions']:
        address = int(row['address'], 16)
        if address in promoted:
            assert row['legacy_model'] == promoted[address]
            assert row['source'] != row['legacy_model']


def test_missing_legacy_model_is_rejected():
    mapping = copy.deepcopy(MAP)
    mapping[next(iter(mapping))]['legacy_model'] = 'tests/models/missing_legacy.c'
    with pytest.raises(ValueError, match='missing or escaping mapped file'):
        build_inventory(mapping=mapping)


def test_inventory_rejects_test_model_as_production_implementation():
    mapping = copy.deepcopy(MAP)
    address = next(key for key, value in mapping.items()
                   if value.get('target_abi') and value['source'].startswith('tests/'))
    mapping[address]['target_abi']['source'] = mapping[address]['source']
    with pytest.raises(ValueError, match='not a production build input'):
        build_inventory(mapping=mapping)


def test_inventory_rejects_missing_mapped_test():
    mapping = copy.deepcopy(MAP)
    address = next(key for key, value in mapping.items() if value.get('target_abi'))
    mapping[address]['target_abi']['tests'] = ['tests/nonexistent_ledger_test.py']
    with pytest.raises(ValueError, match='missing or escaping mapped file'):
        build_inventory(mapping=mapping)


def test_inventory_requires_exact_static_mapping():
    mapping = dict(MAP)
    mapping.pop(next(iter(mapping)))
    with pytest.raises(ValueError, match='inventory and curated mapping disagree'):
        build_inventory(mapping=mapping)


def test_checkpoint_tracks_source_edits_and_partial_invocation(tmp_path):
    path = tmp_path / 'checkpoint.json'
    inputs = {'src/module.c': 'first-revision'}
    checkpoint = dict(reference_sha256=EXPECTED, pytest_exitstatus=0,
                      input_sha256=inputs, inputs_unchanged_during_run=True,
                      invocation=['pytest', '-k', 'single_case'], test_counts={'passed': 1})
    path.write_text(json.dumps(checkpoint))
    result = checkpoint_status(path, inputs)
    assert result['status'] == 'passed_for_recorded_invocation'
    assert result['invocation'] == checkpoint['invocation']
    edited = dict(inputs, **{'src/module.c': 'second-revision'})
    result = checkpoint_status(path, edited)
    assert result['status'] == 'stale'
    assert result['changed_since_checkpoint'] == ['src/module.c']
    for changed in ({}, dict(inputs, **{'src/new.c': 'added'})):
        assert checkpoint_status(path, changed)['status'] == 'stale'
    checkpoint['pytest_exitstatus'] = 1
    path.write_text(json.dumps(checkpoint))
    assert checkpoint_status(path, inputs)['status'] == 'failed'


@pytest.mark.parametrize('missing', ['input_sha256', 'inputs_unchanged_during_run'])
def test_incomplete_checkpoint_does_not_claim_current_success(tmp_path, missing):
    checkpoint = dict(reference_sha256=EXPECTED, pytest_exitstatus=0,
                      input_sha256={}, inputs_unchanged_during_run=True)
    del checkpoint[missing]
    path = tmp_path / 'checkpoint.json'
    path.write_text(json.dumps(checkpoint))
    assert checkpoint_status(path, {})['status'] == 'unverified_inputs'


def test_reference_mismatch_is_rejected(tmp_path):
    path = tmp_path / 'checkpoint.json'
    path.write_text(json.dumps({'reference_sha256': 'different-image'}))
    with pytest.raises(ValueError, match='different reference'):
        checkpoint_status(path, {})
    assert checkpoint_status(None, {})['status'] == 'not_supplied'


def test_cli_generates_consistent_index_without_historical_proofs(tmp_path):
    # A fresh index needs current mappings only, not stale hashes or optional Z3 reports.
    output = tmp_path / 'ledger'
    subprocess.run([sys.executable, str(ROOT / 'tools/reconstruction_ledger.py'),
                    '--output', str(output)], check=True, capture_output=True, text=True)
    ledger = json.loads((output / 'reconstruction-ledger.json').read_text())
    assert ledger['checkpoint']['status'] == 'not_supplied'
    assert (output / 'reconstruction-ledger.md').read_text() == markdown(ledger)
    assert ledger['summary']['identified_functions'] == len(ledger['functions'])
    assert all(row['proof_status'] == 'not_assessed' for row in ledger['functions'])
    assert ledger['mapping_input_sha256']
