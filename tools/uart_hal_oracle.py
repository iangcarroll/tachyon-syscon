"""UART setup/teardown original instructions and passive register semantics."""
from collections import deque
import struct
from unicorn import UC_MEM_READ
from pwm_oracle import PwmOracle

class UartHalOracle(PwmOracle):
    BASES=PwmOracle.BASES+(0x40100000,0x40108000,0xe000e000)
    PORTS=0x20000234
    CONFIG=0x20000762
    RINGS=0x20000774
    def __init__(self,registers=None):
        self.read_scripts={}
        super().__init__(registers)

    def _mmio(self,uc,access,address,size,value,extra):
        if access==UC_MEM_READ and self.read_scripts.get(address):
            supplied=self.read_scripts[address].popleft()
            uc.mem_write(address,struct.pack('<I',supplied))
            self.registers[address]=supplied
        super()._mmio(uc,access,address,size,value,extra)
