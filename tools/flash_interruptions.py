"""Whole-image recovery at atomic FLASHCTL commit boundaries.

The digital model makes each sector erase/eight-byte program atomic. We record
every committed prefix, then supply it to a fresh CPU/peripheral environment.
This models loss of volatile state, not torn cells, ECC, or analog brownouts.
Observers wrap only the model's storage sink; guest code and MMIO results run
unchanged. Repeated identical flash images need only one fresh-boot replay.
"""
import gc
import hashlib
import re
from functools import reduce
from operator import xor
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_MSP, UC_ARM_REG_R2, UC_ARM_REG_R3

from functional_scenarios import PowerTransitions
from rebuilt_system import boot, command_reply, normalized_log

IDENTITY = 0xf800
CONFIG = 0xfc00
SLOT_BYTES = 64
SLOTS = 15
OLD_KEY = b'checkpoint.key.' + b'k' * 15
NEW_KEY = b'pending.key.' + b'k' * 18
OLD_VALUE = b'old_' + b'o' * 26
NEW_VALUE = b'new_' + b'n' * 26


def slot(key, value):
    """Construct the documented 2x32-byte slot as an explicit test input."""
    fields = []
    for text in (key, value):
        if not isinstance(text, bytes) or not re.fullmatch(rb'[A-Za-z0-9_.-]{1,30}', text):
            raise ValueError('Fixture fields must be 1..30 plain configuration bytes')
        field = (text + b'\0').ljust(31, b'\xff')
        fields.append(field + bytes([reduce(xor, field, 0)]))
    return b''.join(fields)


def fixture(image, case):
    if case not in ('append', 'compact'):
        raise ValueError('Unknown flash interruption case')
    if len(image) > 65536:
        raise ValueError('Oversized flash image')
    result = bytearray(image.ljust(65536, b'\xff'))
    result[IDENTITY:CONFIG] = (slot(b'confVersion', b'1') +
                               slot(b'fixture.serial', b'synthetic')).ljust(1024, b'\xff')
    previous = slot(OLD_KEY, OLD_VALUE) * (14 if case == 'compact' else 1)
    # The unused final 64 bytes belong to the same erase sector. The pattern
    # distinguishes a sector erase from an incorrectly modeled 960-byte erase.
    result[CONFIG:] = (slot(b'confVersion', b'1') + previous).ljust(960, b'\xff') + b'\xa5' * 64
    return bytes(result)


def lookup(page, key):
    """Legacy GET's observable rule: last exact key wins, even with bad CRC.

    This intentionally does not substitute a safer checksum-valid-slot rule.
    Readback truncates to 30 bytes and terminates at NUL or semicolon.
    """
    if len(page) != 1024:
        raise ValueError('Expected one configuration sector')
    for offset in range((SLOTS - 1) * SLOT_BYTES, -1, -SLOT_BYTES):
        if page[offset:offset + len(key) + 1] == key + b'\0':
            return page[offset + 32:offset + 62].split(b'\0')[0].split(b';')[0]
    return None


def expected_after_boot(page):
    # Startup uses GET(confVersion) as a presence test, not a version/CRC test.
    if lookup(page, b'confVersion') is None:
        return slot(b'confVersion', b'1').ljust(1024, b'\xff')
    return page


def stack_log(reply, observations):
    """Validate actual stack measurements before abstracting private frame sizes."""
    pattern = rb'(?m)^\[TIME\] \[CONF\] Compaction: (\d+) bytes of stack in use\r$'
    values = [int(value) for value in re.findall(pattern, reply)]
    if values != [row['reported'] for row in observations]:
        raise AssertionError('Stack diagnostic does not match observed logger calls')
    for row in observations:
        if row['reported'] != 0x20001000 - row['msp']:
            raise AssertionError('Compaction stack diagnostic is not the actual stack depth')
    return re.sub(pattern, b'[TIME] [CONF] Compaction: [STACK_DEPTH] bytes of stack in use\r', reply)


def capture(image, case, floor, logger_entry):
    # Collect prior inactive Unicorn engines outside guest execution; finalizing
    # a previous JIT during another engine's callback is unsafe on macOS.
    gc.collect()
    initial = fixture(image, case)
    machine, _ = boot(initial, stack_floor=floor)
    if bytes(machine.flash) != initial:
        raise AssertionError('Constructed initialized namespaces changed during boot')
    snapshots = [initial]
    operations = []
    stack = []
    controller_start = len(machine.device.flash.events)
    sink = machine.device.flash.write_flash

    def observe_logger(cpu, address, size, unused):
        if address != logger_entry & ~1:
            return
        fmt = bytes(cpu.mem_read(cpu.reg_read(UC_ARM_REG_R2), 64)).split(b'\0')[0]
        if fmt == b'Compaction: %d bytes of stack in use':
            stack.append(dict(msp=cpu.reg_read(UC_ARM_REG_MSP), reported=cpu.reg_read(UC_ARM_REG_R3)))

    logger_hook = machine.cpu.hook_add(UC_HOOK_CODE, observe_logger,
                                       begin=logger_entry & ~1, end=logger_entry & ~1)

    def committed(address, data):
        # Forward the real model mutation exactly once before observing it.
        sink(address, data)
        after = bytes(machine.flash)
        if not CONFIG <= address < address + len(data) <= 65536:
            raise AssertionError('Runtime update wrote outside its configuration sector')
        if after[:CONFIG] != initial[:CONFIG]:
            raise AssertionError('Application or identity changed')
        if len(data) not in (8, 1024):
            raise AssertionError('Unexpected atomic flash mutation size')
        operations.append(dict(kind='erase' if len(data) == 1024 else 'program',
                               address=address, data=data.hex()))
        snapshots.append(after)

    machine.device.flash.write_flash = committed
    key = OLD_KEY if case == 'append' else NEW_KEY
    try:
        reply = command_reply(machine, 'CONFIG_SET ' + key.decode() + ' ' + NEW_VALUE.decode())
    finally:
        machine.device.flash.write_flash = sink
        machine.cpu.hook_del(logger_hook)
    if b'[MFGD] PASS\r\n' not in reply or lookup(bytes(machine.flash[CONFIG:]), key) != NEW_VALUE:
        raise AssertionError('Uninterrupted update did not succeed')
    kinds = [operation['kind'] for operation in operations]
    if case == 'append':
        if kinds != ['program'] * 8:
            raise AssertionError('Append did not execute a complete eight-word slot write')
    elif kinds != ['erase'] * 15 + ['program'] * 24:
        # Original erase loop issues 15 sector erases at 64-byte-spaced addresses,
        # then compaction restores new key, latest old key, and confVersion.
        raise AssertionError('Compaction did not erase and restore all three entries')
    unique = {}
    for boundary, snapshot in enumerate(snapshots):
        unique.setdefault(snapshot, []).append(boundary)
    return dict(case=case, operations=operations, snapshots=snapshots,
                controller=[(kind, address, data.hex(), status) for kind, address, data, status
                            in machine.device.flash.events[controller_start:]],
                unique=[dict(image=image, boundaries=boundaries) for image, boundaries in unique.items()],
                stack=stack, raw_reply=reply.hex(), reply=stack_log(normalized_log(reply), stack).hex())


def compare_captures(original, rebuilt):
    if original['case'] != rebuilt['case'] or original['operations'] != rebuilt['operations']:
        raise AssertionError('Flash command sequence differs')
    if original['controller'] != rebuilt['controller']:
        raise AssertionError('Flash controller transactions differ')
    if original['reply'] != rebuilt['reply']:
        raise AssertionError('Uninterrupted protocol output differs')
    a, b = original['snapshots'], rebuilt['snapshots']
    if len(a) != len(b) or any(x[IDENTITY:] != y[IDENTITY:] for x, y in zip(a, b)):
        raise AssertionError('Persistent flash differs at an interruption boundary')
    if [row['boundaries'] for row in original['unique']] != [row['boundaries'] for row in rebuilt['unique']]:
        raise AssertionError('Identical-input replay groups differ')


def recover(snapshot, floor):
    gc.collect()
    expected = expected_after_boot(snapshot[CONFIG:])
    power = PowerTransitions()
    machine, _ = boot(snapshot, stack_floor=floor, observer=lambda m: power.attach(m, 'recovery'))
    if bytes(machine.flash[:CONFIG]) != snapshot[:CONFIG]:
        raise AssertionError('Recovery modified application or identity')
    if bytes(machine.flash[CONFIG:]) != expected:
        raise AssertionError('Recovered sector violates the independent initialization rule')
    replies = []
    for key in (OLD_KEY, NEW_KEY, b'confVersion'):
        output = command_reply(machine, 'CONFIG_GET ' + key.decode())
        value = lookup(expected, key)
        if value is None:
            if b'[MFGD] FAIL\r\n' not in output:
                raise AssertionError('Missing key unexpectedly readable')
        elif b'[MFGD] PASS\r\n' not in output or key + b' = ' + value + b'\r\n' not in output:
            raise AssertionError('Recovered readback does not match persisted bytes')
        replies.append(normalized_log(output).hex())
    version = command_reply(machine, 'VERSION')
    if b'Version=1.0.52\r\n' not in version or b'PASS\r\n' not in version:
        raise AssertionError('Recovered firmware is not responsive')
    if bytes(machine.flash[:CONFIG]) != snapshot[:CONFIG] or bytes(machine.flash[CONFIG:]) != expected:
        raise AssertionError('Read-only recovery checks mutated flash')
    return dict(replies=replies, version=normalized_log(version).hex(),
                persistent=bytes(machine.flash[IDENTITY:]).hex(), power=power.events,
                boot=normalized_log(bytes(machine.device.tx[0])).hex(),
                flash=[(kind, address, data.hex(), status) for kind, address, data, status in machine.device.flash.events])


def report(captured):
    """Keep replay metadata/persistent bytes, never copy original code into reports."""
    return dict(case=captured['case'], operations=captured['operations'], controller=captured['controller'],
                stack=captured['stack'], raw_reply=captured['raw_reply'],
                boundary_count=len(captured['snapshots']),
                unique=[dict(boundaries=row['boundaries'],
                             image_sha256=hashlib.sha256(row['image']).hexdigest(),
                             persistent=row['image'][IDENTITY:].hex()) for row in captured['unique']])
