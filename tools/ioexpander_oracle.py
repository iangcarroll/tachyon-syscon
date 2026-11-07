"""Original IO-expander instructions, with I2C HAL and fatal-assertion boundaries.

Register storage is a deterministic test double, not an electrical peripheral
simulation. Short transfers leave registers unchanged in this particular model.
"""
from collections import deque
from oracle import Oracle


class IoAssertion(Exception):
    pass


class RegisterBus:
    def __init__(self, registers):
        self.registers = bytearray(registers)
        self.pointer = 0
        self.events = []
        self.results = {kind: deque() for kind in ('init', 'write', 'read')}

    def result(self, kind, default):
        return self.results[kind].popleft() if self.results[kind] else default

    def init(self, bus, config):
        result = self.result('init', 0)
        self.events.append(('init', bus, bytes(config), result))
        return result

    def write(self, bus, address, data):
        data = bytes(data)
        result = self.result('write', len(data))
        self.events.append(('write', bus, address, data, result))
        if result == len(data):
            self.pointer = data[0]
            for index, value in enumerate(data[1:]):
                self.registers[(self.pointer + index) & 255] = value
        return result

    def read(self, bus, address, count):
        result = self.result('read', count)
        value = bytes(self.registers[(self.pointer+i) & 255] for i in range(count))
        self.events.append(('read', bus, address, count, result, value if result == count else None))
        return result, value

    def assertion(self, line):
        self.events.append(('assert', line))

    def invalid(self, pin):
        self.events.append(('invalid-output', pin))

    def gpio_read(self, pin):
        self.events.append(('gpio-read', pin))
        return pin & 1

    def gpio_write(self, pin, value):
        self.events.append(('gpio-write', pin, value))


class IoOracle(Oracle):
    INITIALIZED = 0x200002d0

    def __init__(self, bus, initialized=1):
        super().__init__()
        self.bus = bus
        self.put(self.INITIALIZED, bytes([initialized]))
        self.hooks.update({0x82f0:self._init, 0x844c:self._write,
                           0x860c:self._read, 0x2678:self._assertion,
                           0x8f88:self._log, 0x80f8:self._gpio_read,
                           0x8054:self._gpio_write})

    def _init(self, o):
        return self.bus.init(o.arg(0), o.cpu.mem_read(o.arg(1), 8))

    def _write(self, o):
        return self.bus.write(o.arg(0), o.arg(1), o.cpu.mem_read(o.arg(2), o.arg(3)))

    def _read(self, o):
        result, value = self.bus.read(o.arg(0), o.arg(1), o.arg(3))
        if result == o.arg(3): o.put(o.arg(2), value)
        return result

    def _assertion(self, o):
        self.bus.assertion(o.arg(1))
        raise IoAssertion(o.arg(1))

    def _log(self, o):
        assert o.cstring(o.arg(2)) == b'IOExpander[P%d]: input, invalid op'
        self.bus.invalid(o.arg(3))

    def _gpio_read(self, o):
        return self.bus.gpio_read(o.arg(0))

    def _gpio_write(self, o):
        self.bus.gpio_write(o.arg(0), o.arg(1))

    def invoke(self, address, *args):
        try:
            result = self.call(address, *args)
            return result if result < 0x80000000 else result - 0x100000000
        except IoAssertion:
            return -2
