"""Exercise real pytest collection and execution across disjoint CI workers."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def run_pytest(tmp_path):
    # This isolated suite cannot import the project's emulator/checkpoint hooks.
    # Each test records execution, so a partition that collects but skips tests
    # cannot satisfy the coverage check.
    (tmp_path / 'test_cases.py').write_text('''
import json
import os
from pathlib import Path
import pytest

@pytest.mark.parametrize('value', range(11))
def test_case(value, request):
    with Path(os.environ['EXECUTED_TESTS']).open('a') as stream:
        stream.write(json.dumps(request.node.nodeid) + '\\n')
''')

    def run(*args):
        recorded = tmp_path / 'executed.jsonl'
        recorded.unlink(missing_ok=True)
        env = {**os.environ, 'PYTHONPATH': str(ROOT / 'tools'),
               'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'EXECUTED_TESTS': str(recorded)}
        for key in ('PYTEST_ADDOPTS', 'PYTEST_PLUGINS'):
            env.pop(key, None)
        result = subprocess.run([sys.executable, '-m', 'pytest', '-p', 'pytest_sharding',
                                 '-q', *args], cwd=tmp_path, env=env,
                                text=True, capture_output=True, timeout=30)
        executed = [json.loads(line) for line in recorded.read_text().splitlines()] if recorded.exists() else []
        return result, executed
    return run


def test_shards_execute_every_case_once_and_preserve_selection(run_pytest):
    for selection in [[], ['-k', 'not case[2]']]:
        full, expected = run_pytest(*selection)
        assert full.returncode == 0, full.stdout + full.stderr
        combined = []
        for index in range(3):
            result, executed = run_pytest(*selection, '--test-shard', f'{index}/3')
            assert result.returncode == 0, result.stdout + result.stderr
            assert executed == sorted(expected)[index::3]
            assert not set(combined).intersection(executed)
            combined.extend(executed)
        assert sorted(combined) == sorted(expected)


@pytest.mark.parametrize('selector', ['-1/3', '3/3', '0/0', '0/-2', '0', 'a/3', '0/3/4'])
def test_invalid_shard_fails_before_executing_tests(run_pytest, selector):
    result, executed = run_pytest('--test-shard=' + selector)
    assert result.returncode == pytest.ExitCode.USAGE_ERROR
    assert '--test-shard' in result.stderr
    assert not executed
