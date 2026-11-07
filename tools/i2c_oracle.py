"""I2C original-instruction oracle with exact scripted MMIO and IRQ injection."""
import struct
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from oracle import Oracle
from adc_oracle import RegisterModel

BASE=0x400f0000
REGISTERS=[BASE+x for x in [0x800,0x804,0x1000,0x1004,0x1020,0x1028,0x1200,0x1210,
    0x1214,0x1218,0x121c,0x1220,0x1224,0x1228,0x1238,0x123c]]
REGISTERS += [0x40428004+i*4 for i in range(32)]
REGISTERS += [0xe000e100,0xe000e280,0x400b040c]

class I2cAssertion(Exception):pass

class I2cRegisterModel(RegisterModel):
    def __init__(self,registers,scripts=None,irq=None):
        super().__init__(registers,scripts)
        self.irq=irq;self.read_counts={};self.set_error=None

    def read(self,address):
        value=super().read(address)
        self.read_counts[address]=self.read_counts.get(address,0)+1
        if self.irq==(address,self.read_counts[address]):
            self.set_error()
            self.events.append(('irq-error',))
        return value

class I2cOracle(Oracle):
    DATA=0x20000900
    def __init__(self,model):
        super().__init__();self.model=model
        self.model.set_error=lambda:self.put(0x20000760,b'\1')
        for page in {a&~0xfff for a in REGISTERS}|{a&~0xfff for a in model.registers}:
            self.cpu.mem_map(page,0x1000)
        self.cpu.hook_add(UC_HOOK_MEM_READ,self._read,begin=0x40000000,end=0xffffffff)
        self.cpu.hook_add(UC_HOOK_MEM_WRITE,self._write,begin=0x40000000,end=0xffffffff)
        self.hooks[0x7ae8]=lambda o:self.model.delay(o.arg(0))
        self.hooks[0x2678]=self._assertion
        self.hooks[0x8f88]=lambda _:None

    def _read(self,uc,access,address,size,value,user):
        assert size==4
        uc.mem_write(address,struct.pack('<I',self.model.read(address)))

    def _write(self,uc,access,address,size,value,user):
        assert size==4
        self.model.write(address,value)

    def _assertion(self,o):
        self.model.assertion(o.arg(1));raise I2cAssertion(o.arg(1))

    def invoke(self,entry,bus=0,address=0,data=None,length=0):
        if data is not None:self.put(self.DATA,data)
        try:
            if entry==0x82f0:return self.call(entry,bus,self.DATA if data is not None else 0,count=2000000)
            if entry==0x82b4:return self.call(entry,0x2000013c,address,count=2000000)
            return self.call(entry,bus,address,self.DATA if data is not None else 0,length,count=2000000)
        except I2cAssertion:return 0xffffffffffffffff
