"""Test-only normalization for linked power-name pointers, never guest patches."""
import re
import struct
from unicorn import UcError


class PowerStateComparison:
    TABLE = 0x20000060
    SIZE = 84

    def __init__(self, original, candidate):
        self.mapping = {}
        if 'syscon_power_names' not in candidate.symbols:
            return
        assert candidate.symbols['syscon_power_names'] == self.TABLE
        for address in range(self.TABLE, self.TABLE + self.SIZE, 4):
            left, right = original.u32(address), candidate.u32(address)
            assert candidate.CODE <= right < candidate.CODE + 0x80000, 'Power name still points at original ROM'
            assert original.cstring(left) == candidate.cstring(right)
            self.mapping[right] = left

    def word(self, address, size, value):
        if self.TABLE <= address and address + size <= self.TABLE + self.SIZE:
            if size == 4 and address % 4 == 0:
                return self.mapping.get(value, value)
        return value

    def memory(self, address, data):
        data = bytearray(data)
        for slot in range(self.TABLE, self.TABLE + self.SIZE, 4):
            if address <= slot and slot + 4 <= address + len(data):
                value = struct.unpack_from('<I', data, slot - address)[0]
                struct.pack_into('<I', data, slot - address, self.mapping.get(value, value))
        return bytes(data)

    def result(self, value):
        high, low = value >> 32, value & 0xffffffff
        return (self.mapping.get(high, high) << 32) | low


def text_argument(cpu, value):
    if value and not (value < 0x10000 or 0x01000000 <= value < 0x01080000
                      or 0x20000000 <= value < 0x20001000):
        return value
    try:
        return cpu.cstring(value)
    except (UcError, ValueError):
        # Corrupt enum tests can pass an unmapped pointer to a replaced logger.
        # Preserve that exact argument, rather than pretending it is a string.
        return value


def log_arguments(cpu, format_index):
    fmt = cpu.cstring(cpu.arg(format_index))
    conversions = re.findall(rb'%(?!%)[-+ #0]*[0-9.*]*[hl]*([diuxXscp])', fmt)
    prefix = tuple(cpu.arg(i) for i in range(format_index))
    if format_index == 2:
        prefix = (prefix[0], text_argument(cpu, prefix[1]))
    values = tuple(text_argument(cpu, cpu.arg(format_index + 1 + i)) if code == b's'
                   else cpu.arg(format_index + 1 + i)
                   for i, code in enumerate(conversions))
    return (*prefix, fmt, *values)
