"""Real child-process checks for the emulator's compiler launcher."""
import os
import subprocess
import sys

import pytest

import toolchain_process


def test_child_input_output_and_failure_are_preserved():
    child = [sys.executable, '-c',
             'import sys; data=sys.stdin.read(); print(data.upper()); '
             'print(data.lower(),file=sys.stderr); sys.exit(7)']
    with pytest.raises(subprocess.CalledProcessError) as failure:
        toolchain_process.run(child, input='MiXeD', text=True, capture_output=True, check=True)
    assert failure.value.returncode == 7
    assert failure.value.stdout.strip() == 'MIXED'
    assert failure.value.stderr.strip() == 'mixed'


def test_child_launch_avoids_fork_with_unicorn_engines():
    # Start with closed inherited descriptors. Other tests may own inheritable
    # handles, in which case the launcher correctly falls back to fork.
    code = """
import os, subprocess, sys
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB
import toolchain_process
engines = [Uc(UC_ARCH_ARM, UC_MODE_THUMB) for _ in range(8)]
for cpu in engines:
    cpu.mem_map(0x20000000, 4096)
def forbidden_fork(*args, **kwargs):
    raise AssertionError('Compiler launch forked the emulator process')
if sys.platform == 'darwin':
    subprocess._fork_exec = forbidden_fork
output = toolchain_process.check_output(
    [sys.executable, '-c', 'import os; print(os.getpid())'], text=True)
assert int(output) != os.getpid()
"""
    env = dict(os.environ, PYTHONPATH=os.path.dirname(toolchain_process.__file__))
    subprocess.run([sys.executable, '-c', code], env=env, check=True, capture_output=True)


def test_private_inheritable_descriptor_is_not_leaked():
    read_fd, write_fd = os.pipe()
    try:
        os.set_inheritable(read_fd, True)
        child = [sys.executable, '-c',
                 'import os,sys\ntry: os.fstat(int(sys.argv[1]))\n'
                 'except OSError: print("closed")\nelse: print("open")', str(read_fd)]
        assert toolchain_process.check_output(child, text=True).strip() == 'closed'
        # Explicit pass_fds still works through the normal subprocess path.
        assert toolchain_process.check_output(child, text=True, pass_fds=(read_fd,)).strip() == 'open'
    finally:
        os.close(read_fd)
        os.close(write_fd)
