"""Strict function-level register model: reads require explicit test values."""
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_WRITE
from oracle import Oracle


class MSPM0CoreOracle(Oracle):
    def __init__(self,registers):
        super().__init__()
        self.registers=dict(registers)
        self.trace=[]
        self.dispatch=[]
        for base,size in [(0x40080000,0x2000),(0x400a0000,0x2000),
                          (0x400b0000,0x1000),(0x40400000,0x2000),
                          (0x40428000,0x1000),(0xe000e000,0x2000)]:
            self.cpu.mem_map(base,size)
            self.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self._access,
                              begin=base,end=base+size-1)
        for fn in (0x10021,0x10025,0x96d5,0x3b35,0x7bb9):
            self.hooks[fn&~1]=lambda o,fn=fn:self._dispatch(fn)

    def _access(self,uc,access,address,size,value,_):
        if size!=4:raise ValueError(f'Unexpected register width{size} at{address:#x}')
        if address not in self.registers:raise ValueError(f'Unmodelled register{address:#x}')
        if access==UC_MEM_WRITE:
            self.registers[address]=value
            self.trace.append(('write',address,value))
        else:
            value=self.registers[address]
            uc.mem_write(address,value.to_bytes(4,'little'))
            self.trace.append(('read',address,value))

    def _dispatch(self,fn):
        args=(self.arg(0),self.arg(1)) if fn<0x10030 and fn>=0x10000 else (0,0)
        self.dispatch.append((fn if fn>=0x10000 else fn&~1,*args))
