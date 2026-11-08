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
ENTRIES={0x82b4:'i2c_error',0x82f0:'i2c_init',0x844c:'i2c_transmit',0x860c:'i2c_receive',0x8798:'i2c_irq',
 0x87dc:'pwm_init',0x88c0:'pwm_write',0x9400:'pwm_clock',0x941c:'pwm_compare',0x942c:'pwm_capture',
 0x9450:'pwm_action',0x9470:'pwm_output',0x948c:'pwm_configure'}
REGIONS=[(0x40080000,0xa000),(0x400a0000,0x2000),
 (0x400b0000,0x2000),(0x400f0000,0x4000),(0x40428000,0x1000),(0xe000e000,0x1000)]
class AssertionBoundary(Exception):pass
class BusBoundary(Exception):pass

def build(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    trap=out/'logger.c';trap.write_text('void syscon_target_logger(unsigned a,const char *b,const char *c,...){(void)a;(void)b;(void)c;__asm__("bkpt #0");}\n')
    sources=[ROOT/'target/i2c_target.c',ROOT/'target/pwm_target.c',ROOT/'target/hal_helpers.c',
        ROOT/'target/mspm0_core_target.c',ROOT/'target/gpio_state.c',ROOT/'target/core_helpers.c',ROOT/'target/fault_control_target.c',
        ROOT/'src/runtime_memory.c',trap]
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
        '-Wl,-T,'+str(ROOT/'target/emulation.ld'),'-Wl,--gc-sections','-Wl,-e,syscon_target_i2c_init',
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
                def string(address):
                    text=bytearray()
                    for offset in range(256):
                        byte=o.cpu.mem_read(address+offset,1)
                        if byte==b'\0':return bytes(text)
                        text.extend(byte)
                    raise AssertionError('Unterminated assertion diagnostic')
                raise AssertionBoundary((string(value[0]),value[1],string(value[2])))
            m.hooks[0x2678 if not i else m.symbols['syscon_target_assert']&~1]=assertion
            def logger(o,index=i):
                args=(o.arg(0),o.cstring(o.arg(1)),o.cstring(o.arg(2)))
                if args[2]==b'I2C timeout: %s':args+=(o.cstring(o.arg(3)),)
                self.events[index].append(('logger',args));return 0
            m.hooks[0x8f88 if not i else m.symbols['syscon_target_logger']&~1]=logger
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
            if entry in (0x82f0,0x860c,0x948c):result|=m.cpu.reg_read(UC_ARM_REG_R1)<<32
            if entry in (0x8798,0x9400,0x941c,0x942c,0x9450,0x9470):result=None
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
