"""Original timer/retained instructions with explicit passive register storage.

The MMIO backing records exact accesses but does not model SysTick progression,
reset domains, interrupt preemption, or retention across electrical power loss.
"""
import struct
from unicorn import UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_MEM_WRITE
from oracle import Oracle


class TimerOracle(Oracle):
    STATE=0x20000610
    RETAINED=0x200000da

    def __init__(self):
        super().__init__()
        self.mmio=[]
        self.callbacks=[]
        self.callback_action=None
        self.hooks[0x8f88]=lambda _:None
        for base in (0xe000e000,0x400b0000):
            self.cpu.mem_map(base,0x1000)
            self.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self._mmio,
                              begin=base,end=base+0xfff)
        for address in (0x10021,0x10025,0x10029,0x1002d,0x10031):
            self.hooks[address&~1]=lambda o,address=address:self._callback(address,o.arg(0))

    def _mmio(self,uc,access,address,size,value,_):
        if access==UC_MEM_WRITE:
            self.mmio.append(('write',address,size,value))
        else:
            self.mmio.append(('read',address,size,int.from_bytes(uc.mem_read(address,size),'little')))

    def _callback(self,address,argument):
        self.callbacks.append((address,argument))
        if self.callback_action:
            self.callback_action(self,address,argument)

    def state(self):
        return bytes(self.cpu.mem_read(self.STATE,112))

    def now(self):
        return struct.unpack('<Q',self.cpu.mem_read(self.STATE+104,8))[0]
