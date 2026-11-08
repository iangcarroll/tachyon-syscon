import ctypes
import os
import subprocess
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))


@pytest.fixture(scope='session')
def lib():
    target = ROOT / f'build/libsyscon-{os.getpid()}.dylib'
    target.parent.mkdir(exist_ok=True)
    subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2',
                    '-shared', '-fPIC', '-I', str(ROOT/'include'),
                    *map(str, [*sorted((ROOT/'tests/models').glob('*.c')),
                               ROOT/'src/runtime/runtime_memory.c', ROOT/'src/runtime/runtime_arithmetic.c',
                               ROOT/'src/drivers/flash_controller.c', ROOT/'src/runtime/format.c']), '-o', str(target)], check=True)
    dll = ctypes.CDLL(str(target))
    for name in ['syscon_checksum31', 'syscon_field_readable', 'syscon_field_writable', 'syscon_slot_valid']:
        getattr(dll, name).argtypes = [ctypes.c_void_p]
        getattr(dll, name).restype = ctypes.c_int
    dll.syscon_slot_encode.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
    dll.syscon_find_legacy.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_char_p]
    return dll


def pytest_sessionstart(session):
    from coverage_report import input_hashes
    session.syscon_initial_inputs=input_hashes()


def pytest_sessionfinish(session,exitstatus):
    from oracle import EXECUTED_ORIGINAL, REPLACED_ENDPOINTS
    from coverage_report import write_report
    reporter=session.config.pluginmanager.get_plugin('terminalreporter')
    counts={name:len(reporter.stats.get(name,[])) for name in ('passed','failed','skipped','error','xfailed','xpassed')}
    counts['collected']=session.testscollected
    write_report(EXECUTED_ORIGINAL,REPLACED_ENDPOINTS,exitstatus,session.syscon_initial_inputs,counts)
