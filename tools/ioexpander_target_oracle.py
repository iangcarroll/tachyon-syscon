"""Reference/target execution with compiled I2C/GPIO/terminal fixture bodies."""
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import UC_HOOK_MEM_WRITE,UC_PROT_READ,UC_PROT_EXEC,UcError
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_PRIMASK
from oracle import Oracle,REPLACED_ENDPOINTS
from power_state_comparison import text_argument
from arm_rebuild_oracle import ArmRebuildOracle
from build_ioexpander_target import DEPENDENCIES,MAPPINGS
E=0x21008000
REGS=0x21008800
CALLEE=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
class Reference(Oracle):
    def __init__(self,elf,a):
        self.redirect={entry:a.symbols[name] for entry,name in DEPENDENCIES.items()}
        super().__init__();self.cpu.mem_map(a.CODE,0x100000);self.cpu.mem_map(a.DATA,0x10000)
        with Path(elf).open('rb') as f:
            for segment in ELFFile(f).iter_segments():
                if segment['p_type']=='PT_LOAD' and segment['p_filesz']:self.put(segment['p_vaddr'],segment.data())
        self.cpu.mem_protect(a.CODE,0x100000,UC_PROT_READ|UC_PROT_EXEC)
        self.cpu.mem_protect(0,0x10000,UC_PROT_READ|UC_PROT_EXEC)
    def _step(self,uc,address,size,_):
        if address in self.redirect:
            REPLACED_ENDPOINTS.add(address);uc.reg_write(UC_ARM_REG_PC,self.redirect[address]);return
        if address<0x10000:super()._step(uc,address,size,_)
    def read(self,address,size):return bytes(self.cpu.mem_read(address,size))
class Pair:
    def __init__(self,elf):
        self.a=ArmRebuildOracle(elf);self.o=Reference(elf,self.a);self.machines=(self.o,self.a);self.writes=[[],[]]
        for i,m in enumerate(self.machines):
            m.put(E,bytes(4096));m.put(E+28,struct.pack('<I',0xffffffff))
            def record(uc,kind,address,size,value,_,index=i):
                if 0x20000000<=address<0x20000d00:self.writes[index].append((address,size,value&((1<<(size*8))-1)))
            m.cpu.hook_add(UC_HOOK_MEM_WRITE,record)
    def put(self,address,data):
        for m in self.machines:m.put(address,data)
    def word(self,address,value):self.put(address,struct.pack('<I',value))
    def events(self,m):return m.read(E+128,m.u32(E)*24)
    def compared_events(self,m):
        events=[]
        for index in range(m.u32(E)):
            row=list(struct.unpack('<6I',m.read(E+128+index*24,24)))
            if row[0]==0x2678:row[1],row[3]=text_argument(m,row[1]),text_argument(m,row[3])
            if row[0]==0x8f88:row[2],row[3]=text_argument(m,row[2]),text_argument(m,row[3])
            events.append(tuple(row))
        return events
    def run(self,entry,*args,terminal=False):
        for m in self.machines:
            m.put(E,bytes(4));m.cpu.reg_write(UC_ARM_REG_PRIMASK,1)
            for i,r in enumerate(CALLEE):m.cpu.reg_write(r,0x76543210+i)
        for writes in self.writes:writes.clear()
        results=[]
        for m,fn in ((self.o,entry),(self.a,MAPPINGS[entry])):
            try:
                results.append(m.call(fn,*args));assert not terminal,'Expected nonreturning assertion/fault'
            except UcError:
                if not terminal:raise
                results.append('terminal')
        assert results[0]==results[1]
        assert self.o.read(0x20000000,0xd00)==self.a.read(0x20000000,0xd00)
        assert self.o.read(REGS,256)==self.a.read(REGS,256)
        assert self.compared_events(self.o)==self.compared_events(self.a)
        assert self.writes[0]==self.writes[1]
        for m in self.machines:
            assert m.cpu.reg_read(UC_ARM_REG_PRIMASK)==1
            if not terminal:assert [m.cpu.reg_read(r) for r in CALLEE]==[0x76543210+i for i in range(len(CALLEE))]
        return results[0]
