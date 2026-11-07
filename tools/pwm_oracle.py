"""PWM original-code oracle with passive, traced MMIO storage."""
import struct
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_WRITE
from oracle import Oracle

class PwmAssertion(Exception): pass

class PwmOracle(Oracle):
    BASES=(0x40080000,0x40084000,0x40088000,0x400a0000,0x40428000)
    BOARD=0x20000148
    def __init__(self,registers=None):
        super().__init__()
        self.trace=[]
        self.registers=dict(registers or {})
        for base in self.BASES:
            self.cpu.mem_map(base,0x2000)
            self.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self._mmio,begin=base,end=base+0x1fff)
        for address,value in self.registers.items(): self.put(address,struct.pack('<I',value))
        self.hooks[0x2678]=self._assertion

    def _mmio(self,uc,access,address,size,value,_):
        if access==UC_MEM_WRITE:
            self.trace.append(('write',address,size,value))
            self.registers[address]=value
        else:
            value=int.from_bytes(uc.mem_read(address,size),'little')
            self.trace.append(('read',address,size,value))

    def _assertion(self,o):
        self.trace.append(('assert',o.arg(1)))
        raise PwmAssertion()

    def invoke(self,address,*args):
        try:return self.call(address,*args)
        except PwmAssertion:return 0xfffffffe
