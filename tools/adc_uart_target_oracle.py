"""Source-only target driver build and explicit register/dependency comparison."""
from pathlib import Path
from collections import deque
import struct
import subprocess
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_READ,UC_MEM_WRITE,UcError,UC_PROT_READ,UC_PROT_EXEC
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1
from oracle import Oracle
from arm_rebuild_oracle import ArmRebuildOracle
ROOT=Path(__file__).resolve().parents[1]
ENTRIES={0x7c54:'adc_init',0x7d54:'adc_temperature',0x7e7c:'adc_raw',0x7f24:'adc_millivolts',
         0x8954:'uart_init',0x8b50:'uart_deinit',0x95f0:'uart_line_config',0x9638:'uart_clock_config'}
REGIONS=[(0x40004000,0x4000),(0x40030000,0x2000),(0x400a0000,0x2000),
         (0x40100000,0x2000),(0x40108000,0x2000),(0x40401000,0x1000),
         (0x40428000,0x1000),(0x4055a000,0x1000),(0x4055c000,0x1000),
         (0x41c40000,0x1000),(0xe000e000,0x1000)]
class AssertionBoundary(Exception):pass
class BusBoundary(Exception):pass

def build(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    trap=out/'assert.c';trap.write_text('void syscon_target_assert(unsigned a,unsigned b,unsigned c){(void)a;(void)b;(void)c;__asm__("bkpt #0");}\n')
    sources=[ROOT/'target/adc_target.c',ROOT/'target/uart_hal_target.c',ROOT/'target/hal_helpers.c',
        ROOT/'target/mspm0_core_target.c',ROOT/'target/core_helpers.c',ROOT/'src/runtime_memory.c',
        ROOT/'src/runtime_arithmetic.c',ROOT/'target/runtime_arithmetic_abi.S',ROOT/'target/runtime_arithmetic_float.c',
        *sorted((ROOT/'vendor/gcc-soft-fp').glob('*.c')),trap]
    objects=[]
    flags=['-std=c11','-mcpu=cortex-m0plus','-mthumb','-mfloat-abi=soft','-ffreestanding','-fno-builtin',
        '-ffunction-sections','-fdata-sections','-Wall','-Wextra','-Werror','-I'+str(ROOT/'include'),'-I'+str(ROOT/'vendor/gcc-soft-fp')]
    for i,source in enumerate(sources):
        obj=out/f'{i}.o';objects.append(str(obj))
        optimize='-O2' if source.name=='runtime_arithmetic.c' or source.parent.name=='gcc-soft-fp' else '-Os'
        extra=['-Wno-type-limits'] if source.name=='floatunsisf.c' else []
        if source.parent.name=='gcc-soft-fp':extra.append('-std=gnu11')
        subprocess.run(['arm-none-eabi-gcc',*flags,optimize,*extra,'-c',str(source),'-o',str(obj)],check=True)
    elf=out/'drivers.elf'
    subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',*objects,
        '-Wl,-T,'+str(ROOT/'target/emulation.ld'),'-Wl,--gc-sections','-Wl,-e,syscon_target_adc_init',
        *['-Wl,--undefined=syscon_target_'+s for s in ENTRIES.values()],'-o',str(elf)],check=True)
    return elf

class Pair:
    def __init__(self,elf):
        self.original=Oracle();self.original.cpu.mem_protect(0,0x10000,UC_PROT_READ|UC_PROT_EXEC)
        self.candidate=ArmRebuildOracle(elf);self.machines=(self.original,self.candidate)
        self.events=[[],[]];self.scripts=[{},{}];self.fail_at=None;self.on_delay=None
        self.delay_count=[0,0];self.assertions=[[],[]]
        for i,m in enumerate(self.machines):
            for base,size in REGIONS:m.cpu.mem_map(base,size)
            m.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self.record(i))
            m.cpu.hook_add(UC_HOOK_CODE,self.code(i))
            def assertion(o,index=i):
                value=tuple(o.arg(n) for n in range(3));self.assertions[index].append(value)
                raise AssertionBoundary(value)
            m.hooks[0x2678 if not i else m.symbols['syscon_target_assert']&~1]=assertion
    def code(self,index):
        def hook(uc,address,size,_):
            m=self.machines[index]
            delay=0x7ae8 if not index else m.symbols['syscon_cycle_delay']&~1
            if address==delay:
                value=uc.reg_read(UC_ARM_REG_R0);self.events[index].append(('delay',value))
                self.delay_count[index]+=1
                if self.on_delay:self.on_delay(m,self.delay_count[index],value)
            data=bytes(uc.mem_read(address,size)) if size==4 else b''
            if data in (b'\xbf\xf3\x4f\x8f',b'\xbf\xf3\x6f\x8f'):
                self.events[index].append(('barrier',data.hex()))
        return hook
    def record(self,index):
        def hook(uc,kind,address,size,value,_):
            if not (0x20000000<=address<0x20000f00 or any(b<=address<b+n for b,n in REGIONS)):return
            if len(self.events[index])==self.fail_at:raise BusBoundary((kind,address,size))
            if kind==UC_MEM_READ:
                script=self.scripts[index].get(address)
                if script:uc.mem_write(address,script.popleft().to_bytes(size,'little'))
                value=int.from_bytes(uc.mem_read(address,size),'little')
            self.events[index].append((kind,address,size,value&((1<<(size*8))-1)))
        return hook
    def put(self,address,data):
        for m in self.machines:m.put(address,data)
    def word(self,address,value):self.put(address,struct.pack('<I',value&0xffffffff))
    def script(self,address,values):
        for s in self.scripts:s[address]=deque(values)
    def execute(self,index,entry,args):
        m=self.machines[index]
        try:
            result=m.call(entry if not index else 'syscon_target_'+ENTRIES[entry],*args,count=3000000)
            if entry==0x7c54:result|=m.cpu.reg_read(UC_ARM_REG_R1)<<32
            if entry in (0x95f0,0x9638):result=None
            return ('return',result)
        except AssertionBoundary as e:return ('assert',e.args)
        except BusBoundary as e:return ('bus-fault',e.args)
        except UcError as e:return ('cpu-fault',e.errno)
    def run(self,entry,*args):
        self.events=[[],[]];self.delay_count=[0,0];self.assertions=[[],[]]
        a=self.execute(0,entry,args);b=self.execute(1,entry,args)
        assert a==b,(hex(entry),args,a,b)
        assert self.events[0]==self.events[1],(hex(entry),args,next(((i,x,y) for i,(x,y) in enumerate(zip(self.events[0],self.events[1])) if x!=y),None),len(self.events[0]),len(self.events[1]))
        assert bytes(self.original.cpu.mem_read(0x20000000,0xf00))==self.candidate.read(0x20000000,0xf00)
        return a
