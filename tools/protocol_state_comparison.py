"""Fixture-only comparison of linked parser callbacks; never edits guest state."""
import struct


class ProtocolStateComparison:
    def __init__(self, original, candidate):
        self.callbacks = {}
        for state, old_context, callback in [
            ('syscon_console_parser', 0x20000048, 'syscon_target_mfg_logger'),
            ('syscon_modem_parser', 0x200000e0, 'syscon_target_sg560d_printf'),
        ]:
            if state not in candidate.symbols:
                continue
            # Unit fixtures share layout; whole-image tests move the objects.
            assert candidate.symbols[state] == old_context
            field = old_context + 16
            pointer = candidate.symbols[callback] | 1
            assert candidate.u32(field) == pointer
            self.callbacks[field] = (pointer, original.u32(field))

    def memory(self, address, data):
        data = bytearray(data)
        for field, (linked, original) in self.callbacks.items():
            if address <= field and field + 4 <= address + len(data):
                offset = field - address
                # An unexpected callback remains different and must fail.
                if struct.unpack_from('<I', data, offset)[0] == linked:
                    struct.pack_into('<I', data, offset, original)
        return bytes(data)
