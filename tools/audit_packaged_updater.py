#!/usr/bin/env python3
"""Inspect a pinned mspm0flash ELF offline; never invoke it or open a device.

Dependencies: pyelftools, unicorn (versions pinned by project requirements.txt).
The only modeled external boundaries are a skipped debug logger and capture of
an outgoing packet before the serial/I2C function. This is not a flashing tool.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import stat
import sys
import zlib

from elftools.elf.elffile import ELFFile
from unicorn import Uc, UC_ARCH_ARM64, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm64_const import (
    UC_ARM64_REG_X0, UC_ARM64_REG_X1, UC_ARM64_REG_X2,
    UC_ARM64_REG_X19, UC_ARM64_REG_X21, UC_ARM64_REG_X30,
    UC_ARM64_REG_SP, UC_ARM64_REG_PC,
)

KNOWN_SHA256 = 'a64185e0623d773c51fa933f82e394375801bd2cfd3a8d49606c3708ec0d48de'
IMAGE_LENGTHS = (1, 1023, 1024, 1025, 63487, 63488, 63489, 64512, 64513, 65536, 65537)
MASK32 = 0xffffffff


class AuditError(RuntimeError):
    pass


def read_pinned_binary(path):
    path = Path(path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or info.st_size > 1024 * 1024:
        raise AuditError('binary must be a regular file no larger than 1 MiB')
    blob = path.read_bytes()
    if hashlib.sha256(blob).hexdigest() != KNOWN_SHA256:
        raise AuditError('binary SHA256 does not match the audited Particle executable')
    return blob


def machine(blob):
    elf = ELFFile(io.BytesIO(blob))
    if elf['e_machine'] != 'EM_AARCH64':
        raise AuditError('expected AArch64 ELF')
    cpu = Uc(UC_ARCH_ARM64, UC_MODE_ARM)
    cpu.mem_map(0, 0x20000)
    cpu.mem_map(0x100000, 0x20000)
    for segment in elf.iter_segments():
        if segment['p_type'] == 'PT_LOAD':
            if segment['p_vaddr'] + segment['p_memsz'] > 0x20000:
                raise AuditError('ELF segment exceeds the fixed offline map')
            cpu.mem_write(segment['p_vaddr'], segment.data())
    cpu.reg_write(UC_ARM64_REG_SP, 0x11f000)
    cpu.reg_write(UC_ARM64_REG_X30, 0x18000)
    return cpu


def padded_length(blob, length):
    """Execute the actual default-padding block, not the entire file loader.

    Empty-file rejection occurs earlier in the loader and is outside this block.
    Only positive 32-bit sizes are accepted here. No file I/O is emulated.
    """
    if not 1 <= length <= MASK32:
        raise AuditError('image length must be a positive 32-bit value')
    cpu = machine(blob)
    cpu.reg_write(UC_ARM64_REG_X21, length)
    cpu.reg_write(UC_ARM64_REG_X19, 0)  # no explicit padding override
    cpu.emu_start(0x305c, 0x3070, count=5)
    if cpu.reg_read(UC_ARM64_REG_PC) != 0x3070:
        raise AuditError('padding block failed to reach its boundary')
    return cpu.reg_read(UC_ARM64_REG_X19)


def range_packet(blob, start, length):
    """Execute the packet helper through its transport-call boundary.

    This deliberately exposes the helper's uint32 wrap semantics, even for zero
    length. Such inputs are NOT authorized flash operations or valid images.
    """
    if not 0 <= start <= MASK32 or not 0 <= length <= MASK32:
        raise AuditError('range helper arguments must fit uint32')
    cpu = machine(blob)
    cpu.reg_write(UC_ARM64_REG_X0, 0x100000)  # synthetic interface object
    cpu.reg_write(UC_ARM64_REG_X1, start)
    cpu.reg_write(UC_ARM64_REG_X2, length)
    captured = []

    def step(uc, pc, size, unused):
        if pc == 0x1bb0:  # printf-style packet logger only
            uc.reg_write(UC_ARM64_REG_PC, uc.reg_read(UC_ARM64_REG_X30))
        elif pc == 0x1d58:  # stop BEFORE UART/I2C transport implementation
            address = uc.reg_read(UC_ARM64_REG_X1)
            count = uc.reg_read(UC_ARM64_REG_X2)
            if count != 16:
                raise AuditError('unexpected range packet length')
            captured.append(bytes(uc.mem_read(address, count)))
            uc.emu_stop()
        elif not (0x26f0 <= pc <= 0x2788 or 0x2150 <= pc <= 0x21fc):
            raise AuditError(f'unexpected execution boundary 0x{pc:x}')

    cpu.hook_add(UC_HOOK_CODE, step)
    cpu.emu_start(0x26f0, 0x18000, count=10000)
    if len(captured) != 1:
        raise AuditError('range helper did not reach its transport boundary')
    return captured[0]


def check_packet(packet, start, length):
    expected_payload = bytes([0x23]) + start.to_bytes(4, 'little') + ((start + length - 1) & MASK32).to_bytes(4, 'little')
    # TI's packet CRC is the uncomplemented reflected CRC32 of the payload.
    expected = b'\x80\x09\x00' + expected_payload + ((zlib.crc32(expected_payload) ^ MASK32) & MASK32).to_bytes(4, 'little')
    if packet != expected:
        raise AuditError('actual range packet differs from independently encoded command/address/end/CRC')
    return {'command': packet[3], 'start': start,
            'inclusive_end': int.from_bytes(packet[8:12], 'little'),
            'packet_hex': packet.hex(), 'crc_checked': True}


def audit(path):
    blob = read_pinned_binary(path)
    cases = []
    for length in IMAGE_LENGTHS:
        padded = padded_length(blob, length)
        if padded != (length + 1023) & ~1023:
            raise AuditError('actual padding differs from the expected 1 KiB rounding')
        packet = check_packet(range_packet(blob, 0, padded), 0, padded)
        cases.append({'image_bytes': length, 'padded_bytes': padded,
                      'reaches_config_at_0xf800': padded > 0xf800,
                      'packet': packet})
    helper_edges = [check_packet(range_packet(blob, start, length), start, length)
                    for start, length in [(0, 0), (MASK32, 1), (MASK32, 2), (0, MASK32)]]
    return {'passed': True, 'binary_sha256': KNOWN_SHA256,
            'hardware_access': False, 'native_updater_execution': False,
            'scope': 'actual padding block and range-packet helper, not complete updater or board validation',
            'image_cases': cases, 'invalid_or_wrapping_helper_inputs': helper_edges,
            'limits': ['zero/wrapping ranges are observations, not safe operations',
                       'transport is trapped before execution; only logging is skipped',
                       'no NONMAIN, password policy, readback, or physical recovery validation']}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary', type=Path, required=True, help='regular-file copy of the pinned Particle mspm0flash ELF')
    parser.add_argument('--output', type=Path, help='JSON output; defaults to stdout; failures replace stale success reports')
    args = parser.parse_args(argv)
    try:
        report = audit(args.binary)
        code = 0
    except Exception as exc:
        report = {'passed': False, 'hardware_access': False, 'error': str(exc)}
        code = 1
    text = json.dumps(report, indent=2) + '\n'
    if args.output:
        args.output.write_text(text)
    else:
        sys.stdout.write(text)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
