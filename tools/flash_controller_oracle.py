"""Register-triggered FLASHCTL model for the image's 64 KiB MAIN geometry.

This is an explicit digital test model, not electrical flash/ECC simulation.
No data changes before CMDEXEC or before a terminal successful status read.
"""
from collections import deque
import struct
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_WRITE
from oracle import Oracle
from config_oracle import ConfigOracle

class FlashControllerModel:
    BASE=0x400cd000
    def __init__(self,read_flash,write_flash,busy=(4,4,0),fail=None):
        self.read_flash,self.write_flash=read_flash,write_flash
        self.registers={self.BASE+x:0xffffffff for x in (0x11d0,0x11d4,0x11d8,0x1210)}
        self.trace=[]
        self.events=[]
        self.busy=tuple(busy)
        self.polls=deque()
        self.pending=None
        self.fail=fail
        self.counts={}

    def write(self,address,value):
        self.trace.append(('write',address,4,value))
        self.registers[address]=value
        if address==self.BASE+0x1100 and value&1:self.start()

    def protected(self,address):
        sector=address//1024
        if sector<32: return bool(self.registers[self.BASE+0x11d0]&(1<<sector))
        # Single-bank MSPM0L130x layout, matching TI DL_FlashCTL_unprotectSector.
        return bool(self.registers[self.BASE+0x11d4]&(1<<((sector-32)//8)))

    def start(self):
        if self.pending is not None: raise ValueError('Overlapping FLASHCTL command')
        typ=self.registers.get(self.BASE+0x1104,0)
        address=self.registers.get(self.BASE+0x1120,0)
        kind={1:'program',2:'erase',6:'blank'}.get(typ&7,'unsupported')
        self.counts[kind]=self.counts.get(kind,0)+1
        data=b''
        status=3
        mutation=None
        if kind=='unsupported' or (kind=='erase' and typ!=0x42) or (kind!='erase' and typ not in (1,6)):
            status=0x1001
        elif address>=65536 or (kind!='erase' and address%8):status=0x41
        elif kind in ('erase','program') and self.protected(address):status=0x11
        elif self.fail==(kind,self.counts[kind]):status=0x1001
        elif kind=='erase':mutation=(address&~1023,b'\xff'*1024)
        elif kind=='blank':
            if self.read_flash(address,8)!=b'\xff'*8:status=0x21
        else:
            data=struct.pack('<II',self.registers.get(self.BASE+0x1130,0),self.registers.get(self.BASE+0x1134,0))
            old=self.read_flash(address,8)
            if self.registers.get(self.BASE+0x1124)!=255:status=0x1001
            elif any((a&b)!=b for a,b in zip(old,data)):status=0x101
            else:mutation=(address,data)
        self.pending=(kind,address,data,status,mutation)
        self.polls=deque([*self.busy,status])

    def read(self,address):
        if address==self.BASE+0x13d0 and self.polls:
            value=self.polls.popleft()
            self.registers[address]=value
            if (value&7) in (1,3) and self.pending is not None:
                kind,offset,data,status,mutation=self.pending
                if value!=status:raise ValueError('Busy script supplied premature terminal status')
                if status&7==3 and mutation:self.write_flash(*mutation)
                self.events.append((kind,offset,data,status))
                self.pending=None
        value=self.registers.get(address,0)
        self.trace.append(('read',address,4,value))
        return value


def attach_controller(oracle,busy=(4,4,0),fail=None):
    model=FlashControllerModel(lambda address,n:bytes(oracle.cpu.mem_read(address,n)),oracle.put,busy,fail)
    oracle.cpu.mem_map(model.BASE,0x2000)
    for address,value in model.registers.items():oracle.put(address,struct.pack('<I',value))
    def mmio(uc,access,address,size,value,_):
        if access==UC_MEM_WRITE:model.write(address,value)
        else:uc.mem_write(address,struct.pack('<I',model.read(address)))
    oracle.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,mmio,begin=model.BASE,end=model.BASE+0x1fff)
    oracle.controller=model
    return model


class FlashControllerOracle(Oracle):
    def __init__(self,busy=(4,4,0),fail=None):
        super().__init__()
        attach_controller(self,busy,fail)


class ConfigControllerOracle(ConfigOracle):
    def __init__(self,initial=None,base=0xfc00,count=15,busy=(4,4,0),fail=None):
        super().__init__(initial,base,count)
        for address in (0x7af4,0x7b10,0x7b44,0x7b60,0x2738):self.hooks.pop(address,None)
        self.controller_diagnostics=[]
        def log(o):
            fmt=o.cstring(o.arg(2))
            if fmt.startswith(b'Flash:'):self.controller_diagnostics.append((o.arg(0),o.cstring(o.arg(1)),fmt))
        self.hooks[0x8f88]=log
        attach_controller(self,busy,fail)
