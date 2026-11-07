"""Run compiled reconstructed ARM C, with callbacks trapped at the ARM ABI.

Original instructions are not mapped executable. Unknown hardware remains
unmapped. This loader does not claim to emulate reset/boot or board peripherals.
"""
import struct
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_MODE_MCLASS,UC_HOOK_CODE,UC_PROT_READ,UC_PROT_EXEC
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
from inventory import load_image

REGISTERS=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3]


class ArmRebuildOracle:
    CODE=0x01000000
    DATA=0x21000000
    TRAPS=0x010ff000
    SENTINEL=0x010fff00
    STATE=0x20000000

    def __init__(self,elf_path):
        self.cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS)
        self.cpu.mem_map(self.CODE,0x100000)
        self.cpu.mem_map(self.DATA,0x10000)
        self.cpu.mem_map(self.STATE,0x1000)
        self.image=load_image()
        # Original rodata pointers retained in recovered control records can be
        # read, but jumping into the original image is explicitly disallowed.
        self.cpu.mem_map(0,0x10000)
        self.cpu.mem_write(0,self.image+b'\xff'*(0x10000-len(self.image)))
        self.cpu.mem_protect(0,0x10000,UC_PROT_READ)
        self.cpu.mem_write(self.STATE,self.image[0xaaf0:0xab20])
        self.cpu.mem_write(self.STATE+0x30,self.image[0xe2e8:0xe578])
        self.symbols={}
        with Path(elf_path).open('rb') as stream:
            elf=ELFFile(stream)
            assert elf.elfclass==32 and elf['e_machine']=='EM_ARM'
            for segment in elf.iter_segments():
                if segment['p_type']!='PT_LOAD':continue
                address=segment['p_vaddr'];size=segment['p_memsz']
                assert segment['p_filesz']<=size
                if not size:continue  # Explicit optional fixture PHDR with no section.
                assert ((self.CODE<=address and address+size<=self.CODE+0x80000) or
                        (self.DATA<=address and address+size<=self.DATA+0x8000) or
                        (any(address==self.STATE+offset and size<=limit for offset,limit in
                             [(0x30,22),(0xb4,36),(0xd8,2),(0x390,24),(0xda,3),(0x534,216),(0x610,112)]) and not segment['p_flags']&1))
                if segment['p_filesz']:self.cpu.mem_write(address,segment.data())
            for symbol in elf.get_section_by_name('.symtab').iter_symbols():
                if symbol['st_shndx']!='SHN_UNDEF':self.symbols[symbol.name]=symbol['st_value']
        self.cpu.mem_protect(self.CODE,0x100000,UC_PROT_READ|UC_PROT_EXEC)
        self.hooks={};self.executed=set();self.hook_calls={}
        self.next_trap=self.TRAPS
        self.next_data=self.DATA+0x8000
        self.cpu.hook_add(UC_HOOK_CODE,self._step)

    def _step(self,uc,address,size,_):
        self.executed.add(address)
        if address in self.hooks:
            self.hook_calls[address]=self.hook_calls.get(address,0)+1
            result=self.hooks[address](self)
            if result is not None:
                uc.reg_write(UC_ARM_REG_R0,result&0xffffffff)
                uc.reg_write(UC_ARM_REG_R1,(result>>32)&0xffffffff)
            uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))

    def callback(self,callback):
        address=self.next_trap;self.next_trap+=4
        assert self.next_trap<self.SENTINEL
        self.hooks[address]=callback
        return address|1

    def allocate(self,data):
        address=(self.next_data+7)&~7
        self.next_data=address+len(data)
        assert self.next_data<self.DATA+0xc000
        self.put(address,data);return address

    def arg(self,index):
        if index<4:return self.cpu.reg_read(REGISTERS[index])
        return self.u32(self.cpu.reg_read(UC_ARM_REG_SP)+4*(index-4))

    def u32(self,address):return struct.unpack('<I',self.cpu.mem_read(address,4))[0]
    def put(self,address,data):self.cpu.mem_write(address,bytes(data))
    def read(self,address,length):return bytes(self.cpu.mem_read(address,length))
    def state(self):return self.read(self.STATE,4096)

    def call(self,symbol,*args,count=500000):
        address=self.symbols[symbol] if isinstance(symbol,str) else symbol
        sp=self.DATA+0xff00
        self.cpu.reg_write(UC_ARM_REG_SP,sp)
        self.cpu.reg_write(UC_ARM_REG_LR,self.SENTINEL|1)
        for i,value in enumerate(args):
            if i<4:self.cpu.reg_write(REGISTERS[i],value&0xffffffff)
            else:self.put(sp+4*(i-4),struct.pack('<I',value&0xffffffff))
        self.cpu.emu_start(address|1,self.SENTINEL,count=count)
        if self.cpu.reg_read(UC_ARM_REG_PC)!=self.SENTINEL:
            raise RuntimeError(f'Compiled ARM instruction budget exhausted at{self.cpu.reg_read(UC_ARM_REG_PC):#x}')
        return self.cpu.reg_read(UC_ARM_REG_R0)
