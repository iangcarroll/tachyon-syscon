"""Execute original ADC code against explicitly provided register values.

No peripheral reset values or readiness transitions are assumed. Unprovided
reads fail. Scripted read sequences permit status changes independently of writes.
"""
import collections
import struct
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from oracle import Oracle

ADC=0x40004000
VREF=0x40030000
REGISTERS=[ADC+x for x in [0x800,0x804,0x808,0x1100,0x1104,0x1108,0x1110,0x1114,0x1180,0x1184,0x1188,0x118c,0x556280,0x556284,0x556288,0x55628c]]
REGISTERS += [VREF+x for x in [0x800,0x804,0x1000,0x1008,0x1100,0x1104,0x1108]]
REGISTERS += [0x40401300,0x41c4003c]

class AdcAssertion(Exception):pass

class RegisterModel:
    def __init__(self,registers,scripts=None):
        self.registers=dict(registers)
        self.scripts={k:collections.deque(v) for k,v in (scripts or {}).items()}
        self.events=[]

    def read(self,address):
        if self.scripts.get(address):value=self.scripts[address].popleft()
        else:
            if address not in self.registers:raise AssertionError(f'Unprovided register {address:#x}')
            value=self.registers[address]
        self.events.append(('read',address,value))
        return value

    def write(self,address,value):
        self.events.append(('write',address,value))
        self.registers[address]=value

    def delay(self,cycles):self.events.append(('delay',cycles))
    def assertion(self,line):self.events.append(('assert',line))

class AdcOracle(Oracle):
    CONFIG=0x20000900
    def __init__(self,model):
        super().__init__()
        self.model=model
        pages={a&~0xfff for a in REGISTERS}|{a&~0xfff for a in model.registers}
        for page in pages:self.cpu.mem_map(page,0x1000)
        self.cpu.hook_add(UC_HOOK_MEM_READ,self._read,begin=0x40000000,end=0x41ffffff)
        self.cpu.hook_add(UC_HOOK_MEM_WRITE,self._write,begin=0x40000000,end=0x41ffffff)
        self.hooks[0x7ae8]=lambda o:self.model.delay(o.arg(0))
        self.hooks[0x2678]=self._assertion

    def _read(self,uc,access,address,size,value,user):
        assert size==4
        uc.mem_write(address,struct.pack('<I',self.model.read(address)))

    def _write(self,uc,access,address,size,value,user):
        assert size==4
        self.model.write(address,value)

    def _assertion(self,o):
        self.model.assertion(o.arg(1));raise AdcAssertion(o.arg(1))

    def invoke(self,entry,pin=0,config=None):
        if config is not None:self.put(self.CONFIG,config)
        try:return self.call(entry,pin,self.CONFIG if config is not None else 0)
        except AdcAssertion:return 0xffffffffffffffff
