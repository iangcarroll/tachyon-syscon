"""Source-compiled original flash ABI, including actual code at SRAM20000000."""
from pathlib import Path
import toolchain_process
import subprocess,struct
from collections import deque
from elftools.elf.elffile import ELFFile
from unicorn import *
from unicorn.arm_const import *
from oracle import Oracle
from power_state_comparison import log_arguments
from arm_rebuild_oracle import ArmRebuildOracle
from flash_controller_oracle import FlashControllerModel
ROOT=Path(__file__).resolve().parents[1]
ENTRIES={0x2738:'flash_report',0x7af4:'flash_erase',0x7b10:'flash_program',0x7b44:'flash_unprotect',0x7b60:'flash_blank',0xaae0:'flash_veneer',0x20000000:'flash_ram_execute'}
def build(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    stub=out/'logger.c';stub.write_text('void syscon_target_logger(void){__asm__("bkpt #0");}\n')
    objects=[]
    for i,source in enumerate([ROOT/'target/drivers/flash_abi_target.c',stub]):
        obj=out/f'{i}.o';objects.append(str(obj))
        toolchain_process.run(['arm-none-eabi-gcc','-std=c11','-mcpu=cortex-m0plus','-mthumb','-Os','-fno-inline','-ffreestanding','-fno-builtin','-Wall','-Wextra','-Werror','-I'+str(ROOT/'include'),'-c',str(source),'-o',str(obj)],check=True)
    elf=out/'flash-abi.elf';toolchain_process.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',*objects,'-Wl,-T,'+str(ROOT/'target/testing/flash_abi_test.ld'),'-o',str(elf)],check=True);return elf
class FlashTargetOracle(ArmRebuildOracle):
    def __init__(self,elf_path):
        self.cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS)
        self.cpu.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M0)
        self.cpu.mem_map(self.CODE,0x100000);self.cpu.mem_map(self.DATA,0x10000);self.cpu.mem_map(self.STATE,4096)
        self.image=(ROOT/'firmware/syscon-1.0.52.bin').read_bytes();self.cpu.mem_map(0,65536,UC_PROT_READ);self.cpu.mem_write(0,self.image)
        self.cpu.mem_write(self.STATE+0x30,self.image[0xe2e8:0xe578]);self.symbols={}
        with Path(elf_path).open('rb') as stream:
            elf=ELFFile(stream)
            for segment in elf.iter_segments():
                if segment['p_type']!='PT_LOAD':continue
                a,n=segment['p_vaddr'],segment['p_memsz']
                assert self.CODE<=a and a+n<=self.CODE+0x80000 or self.DATA<=a and a+n<=self.DATA+0x8000 or self.STATE<=a and a+n<=self.STATE+48
                if segment['p_filesz']:self.cpu.mem_write(a,segment.data())
            for s in elf.get_section_by_name('.symtab').iter_symbols():
                if s['st_shndx']!='SHN_UNDEF':self.symbols[s.name]=s['st_value']
        self.cpu.mem_protect(self.CODE,0x100000,UC_PROT_READ|UC_PROT_EXEC)
        self.hooks={};self.executed=set();self.hook_calls={};self.next_trap=self.TRAPS;self.next_data=self.DATA+0x8000
        self.cpu.hook_add(UC_HOOK_CODE,self._step)
class Boundary(Exception):pass
class Pair:
    def __init__(self,elf,model=False):
        self.machines=(Oracle(),FlashTargetOracle(elf));self.machines[0].cpu.mem_protect(0,65536,UC_PROT_READ|UC_PROT_EXEC);self.events=[[],[]];self.scripts=[{},{}];self.fail_at=None;self.models=[]
        for i,m in enumerate(self.machines):
            m.cpu.mem_map(0x400cd000,0x3000)
            if model:self.models.append(FlashControllerModel(lambda a,n,m=m:bytes(m.cpu.mem_read(a,n)),m.put))
            m.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self.memory(i))
            m.hooks[0x8f88 if not i else m.symbols['syscon_target_logger']&~1]=lambda o,i=i:self.events[i].append(('log',*log_arguments(o,2)))
    def memory(self,i):
        def hook(uc,kind,a,size,value,_):
            if not(0x400cd000<=a<0x400d0000 or 0x20000030<=a<0x20000e00):return
            if self.fail_at==len(self.events[i]):raise Boundary()
            if kind==UC_MEM_READ:
                if self.models and a>=0x400cd000:uc.mem_write(a,struct.pack('<I',self.models[i].read(a)))
                elif self.scripts[i].get(a):uc.mem_write(a,self.scripts[i][a].popleft().to_bytes(size,'little'))
                value=int.from_bytes(uc.mem_read(a,size),'little')
            elif self.models and a>=0x400cd000:self.models[i].write(a,value)
            self.events[i].append((kind,a,size,value&((1<<(size*8))-1)))
        return hook
    def put(self,a,data):
        for m in self.machines:m.put(a,data)
    def word(self,a,value):self.put(a,struct.pack('<I',value&0xffffffff))
    def script(self,a,values):
        for s in self.scripts:s[a]=deque(values)
    def execute(self,i,entry,args):
        m=self.machines[i]
        try:
            result=m.call(entry if not i else 'syscon_target_'+ENTRIES[entry],*args,count=100000)
            return ('return',None if entry==0x2738 else result)
        except Boundary:return ('boundary',)
        except UcError as e:return ('fault',e.errno)
    def run(self,entry,*args):
        self.events=[[],[]];a=self.execute(0,entry,args);b=self.execute(1,entry,args)
        assert a==b,(hex(entry),args,a,b)
        assert self.events[0]==self.events[1],(hex(entry),args,self.events)
        if self.models:assert self.models[0].events==self.models[1].events
        return a
