"""Original UART ring routines with explicitly supplied register events."""
import struct
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_READ
from oracle import Oracle

BASES=[0x40108000,0x40100000]
OFFSETS={0x1020,0x1028,0x1108,0x1120,0x1124}

class Registers:
    def __init__(self):
        self.values={b+x:0 for b in BASES for x in OFFSETS}
        self.trace=[];self.busy=0
    def read(self,address):
        assert address in self.values,f'Unmodeled UART register {address:#x}'
        value=self.values[address]
        if address in [b+0x1108 for b in BASES] and self.busy:
            self.busy-=1;value|=0x80
        self.trace.append(('read',address,value));return value
    def write(self,address,value):
        assert address in self.values,f'Unmodeled UART register {address:#x}'
        self.trace.append(('write',address,value));self.values[address]=value

def attach_registers(o,registers):
    for base in BASES: o.cpu.mem_map(base,0x2000)
    def access(cpu,kind,address,size,value,_):
        assert size==4
        if kind==UC_MEM_READ: cpu.mem_write(address,struct.pack('<I',registers.read(address)))
        else: registers.write(address,value)
    for base in BASES:
        o.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,access,begin=base,end=base+0x1fff)

class UartOracle(Oracle):
    def __init__(self):
        super().__init__();self.registers=Registers();attach_registers(self,self.registers)
    def state(self):
        return bytes(self.cpu.mem_read(0x20000774,152))+bytes(self.cpu.mem_read(0x2000076a,1))+bytes(self.cpu.mem_read(0x20000773,1))+b'\0\0'
