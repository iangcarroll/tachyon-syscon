"""Execute pinned original Thumb code locally; unknown hardware accesses fail closed.

This is a function-level CPU oracle, not a complete MSPM0 board emulator.
Hooks explicitly replace environmental dependencies and are recorded per test.
"""
import struct
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
from inventory import load_image, command_table

REGS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3]
# Session aggregates distinguish executed reference instructions from replaced hooks.
EXECUTED_ORIGINAL = set()
REPLACED_ENDPOINTS = set()


class Oracle:
    SENTINEL = 0x10000

    def __init__(self):
        self.image = load_image()
        self.cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
        self.cpu.mem_map(0, 0x11000)
        self.cpu.mem_write(0, self.image + b'\xff' * (0x10000-len(self.image)))
        self.cpu.mem_map(0x20000000, 0x1000)
        # Reset_Handler's actual RAM copy regions, no fabricated peripheral state.
        self.cpu.mem_write(0x20000000, self.image[0xaaf0:0xab20])
        self.cpu.mem_write(0x20000030, self.image[0xe2e8:0xe578])
        self.hooks = {}
        self.executed = set()
        self.hook_calls = {}
        self.cpu.hook_add(UC_HOOK_CODE, self._step)

    def _step(self, uc, address, size, _):
        self.executed.add(address)
        if address in self.hooks:
            REPLACED_ENDPOINTS.add(address)
            self.hook_calls[address] = self.hook_calls.get(address, 0) + 1
            value = self.hooks[address](self)
            if value is not None:
                uc.reg_write(UC_ARM_REG_R0, value & 0xffffffff)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        else:
            EXECUTED_ORIGINAL.add(address)

    def arg(self, i):
        return self.cpu.reg_read(REGS[i]) if i < 4 else self.u32(self.cpu.reg_read(UC_ARM_REG_SP) + 4 * (i-4))

    def u32(self, address):
        return struct.unpack('<I', self.cpu.mem_read(address, 4))[0]

    def put(self, address, data):
        self.cpu.mem_write(address, bytes(data))

    def cstring(self, address, limit=1024):
        if not address:
            return None
        result = bytearray()
        for i in range(limit):
            b = self.cpu.mem_read(address+i, 1)[0]
            if b == 0:
                return bytes(result)
            result.append(b)
        raise ValueError(f'unterminated string at {address:#x}')

    def call(self, address, *args, count=200000):
        sp = 0x20000ff0
        self.cpu.reg_write(UC_ARM_REG_SP, sp)
        self.cpu.reg_write(UC_ARM_REG_LR, self.SENTINEL | 1)
        for i, value in enumerate(args):
            if i < 4:
                self.cpu.reg_write(REGS[i], value & 0xffffffff)
            else:
                self.put(sp + 4*(i-4), struct.pack('<I', value & 0xffffffff))
        self.cpu.emu_start(address | 1, self.SENTINEL, count=count)
        if self.cpu.reg_read(UC_ARM_REG_PC) != self.SENTINEL:
            raise RuntimeError(f'Instruction budget exhausted at {self.cpu.reg_read(UC_ARM_REG_PC):#x}')
        return self.cpu.reg_read(UC_ARM_REG_R0)


class ProtocolOracle(Oracle):
    CONTEXT = 0x20000048
    BUFFER = 0x20000300
    PRINT = 0x10010

    def __init__(self, handler_result=1, echo=False, enabled=True):
        super().__init__()
        self.pending = bytearray()
        self.events = []
        self.result = handler_result
        self.put(self.CONTEXT, struct.pack('<B3xIIBB2xI', 0, self.BUFFER, 0, echo, enabled, self.PRINT | 1))
        self.hooks[0x8cf0] = lambda o: len(self.pending)
        self.hooks[0x8de4] = lambda o: self.pending.pop(0)
        self.hooks[0x8f88] = lambda o: None  # Diagnostic logging, separate UART side channel.
        self.hooks[0x8c34] = self._echo
        self.hooks[self.PRINT] = self._print
        for entry in command_table(self.image):
            handler = entry['handler']
            self.hooks[handler] = self._handler

    def _echo(self, o):
        self.events.append(('echo', o.arg(1)))

    def _print(self, o):
        # Parser-only output is raw strings. Actual handler printf is not mocked here.
        self.events.append(('print', o.cstring(o.arg(0)).decode('latin1')))

    def _handler(self, o):
        arg = o.cstring(o.arg(0))
        self.events.append(('dispatch', o.cpu.reg_read(UC_ARM_REG_PC), None if arg is None else arg.decode('latin1')))
        return self.result

    def feed(self, data):
        self.pending.extend(data)
        self.call(0x49d0, self.CONTEXT)
        return self.events


if __name__ == '__main__':
    oracle = ProtocolOracle()
    print(oracle.feed(b'Version\r\nCONFIG_SET sys.auto_boot true\n'))
