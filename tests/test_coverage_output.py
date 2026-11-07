"""Normal test runs retain evidence without changing historical Git snapshots."""
import json
from pathlib import Path

import coverage_report


def test_reports_preserve_history_and_support_ci_destination(tmp_path, monkeypatch):
    monkeypatch.setattr(coverage_report, 'ROOT', tmp_path)
    monkeypatch.delenv('SYSCON_COVERAGE_OUTPUT', raising=False)
    analysis = tmp_path / 'analysis'
    analysis.mkdir()
    (analysis / 'listing.txt').write_text('00000100 nop\n00000102 bx lr\n')
    (analysis / 'functions.tsv').write_text('address\tname\n00000100\tfixture\n')
    (analysis / 'function-ranges.tsv').write_text(
        'function\tstart\tend_inclusive\n00000100\t00000100\t00000102\n')
    historical = analysis / 'test-instruction-coverage.json'
    historical.write_text('historical evidence\n')
    coverage_report.write_report({0x100}, set(), 0)
    default = tmp_path / 'build/test-instruction-coverage.json'
    report = json.loads(default.read_text())
    assert report['exercised_identified_instructions'] == 1
    assert report['functions'][0]['missing_instructions'] == ['0x102']
    ci = tmp_path / 'build/ci/report.json'
    monkeypatch.setenv('SYSCON_COVERAGE_OUTPUT', str(ci))
    coverage_report.write_report({0x100, 0x102}, {0x200}, 1)
    second = json.loads(ci.read_text())
    assert second['exercised_identified_instructions'] == 2
    assert second['pytest_exitstatus'] == 1
    assert second['replaced_endpoint_addresses'] == ['0x200']
    assert json.loads(default.read_text()) == report
    assert historical.read_text() == 'historical evidence\n'
    assert len(list((tmp_path / 'build/coverage-runs').glob('*.json'))) == 2
    assert not list(ci.parent.glob('*.tmp'))
