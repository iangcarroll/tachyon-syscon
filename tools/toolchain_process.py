"""Launch build tools without copying Unicorn's mappings on macOS.

CPython can use posix_spawn when the executable has a path and descriptor
closing is unnecessary. Its normal fork path gets very slow after many MCU
engines have been created. Keep subprocess semantics, including closed private
descriptors; fall back to the default when an inheritable descriptor exists.
"""
import errno
import os
import shutil
import subprocess
import sys


def _no_inheritable_descriptors():
    try:
        for name in os.listdir('/dev/fd'):
            if not name.isdecimal() or int(name) <= 2:
                continue
            try:
                if os.get_inheritable(int(name)):
                    return False
            except OSError as error:
                # listdir's own descriptor is already closed.
                if error.errno != errno.EBADF:
                    return False
    except OSError:
        return False
    return True


def _options(command, options):
    options = dict(options)
    if (sys.platform == 'darwin' and isinstance(command, (list, tuple)) and command
            and not options.get('shell') and not options.get('pass_fds')
            and 'close_fds' not in options and 'executable' not in options
            and _no_inheritable_descriptors()):
        executable = shutil.which(command[0], path=os.pathsep.join(os.get_exec_path(options.get('env'))))
        if executable:
            options.update(executable=os.path.abspath(executable), close_fds=False)
    return options


def run(command, **options):
    return subprocess.run(command, **_options(command, options))


def check_output(command, **options):
    return subprocess.check_output(command, **_options(command, options))
