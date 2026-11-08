"""Compare linked stdio placeholder pointers in isolated runtime fixtures."""
import struct


class RuntimeStateComparison:
    def __init__(self, original, candidate):
        self.fields = {}
        if 'syscon_runtime_context' not in candidate.symbols:
            return
        context = candidate.symbols['syscon_runtime_context']
        assert context == 0x2000025c
        for offset, symbol in [(4, 'syscon_stdio_input'), (8, 'syscon_stdio_output'),
                               (12, 'syscon_stdio_error')]:
            field = context + offset
            linked = candidate.symbols[symbol]
            assert candidate.u32(field) == linked
            old = original.u32(field)
            assert bytes(original.cpu.mem_read(old, 32)) == candidate.read(linked, 32)
            self.fields[field] = (linked, old)

    def memory(self, address, data):
        data = bytearray(data)
        for field, (linked, old) in self.fields.items():
            if address <= field and field + 4 <= address + len(data):
                offset = field - address
                if struct.unpack_from('<I', data, offset)[0] == linked:
                    struct.pack_into('<I', data, offset, old)
        return bytes(data)
