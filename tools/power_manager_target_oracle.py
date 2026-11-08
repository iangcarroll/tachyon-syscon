"""Actual original/Cortex-M0+ manager bodies with declared leaf dependencies."""
from pathlib import Path
import toolchain_process
import subprocess,struct,re
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_READ,UcError
from unicorn.arm_const import UC_ARM_REG_R1,UC_ARM_REG_SP
from oracle import Oracle
from arm_rebuild_oracle import ArmRebuildOracle
from power_oracle import PowerEnvironment
from power_state_comparison import PowerStateComparison,log_arguments,text_argument
ROOT=Path(__file__).resolve().parents[1]
ENTRIES=dict(zip([0x4c50,0x4ca8,0x4d00,0x4d58,0x4d68,0x4d9c,0x4df4,0x4e04,0x4e34,0x4ec4,0x4ed4,0x4ee0,0x4fd0,0x5004,0x5048,0x50f4,0x5148,0x517c,0x51c0,0x5264,0x5274],['measure','battery_route','vbus_route','battery_id','battery_id_set','header_route','ntc','ntc_set','battery_route_set','boost','boost_set','header_route_set','header_default','usb_isolate','vbus_route_set','usb_release_callback','usb_assert_callback','usb_reattach_busy','usb_reattach_request','ntc_detection_set_disabled','battery_probe']))
SYMBOLS={entry:('syscon_target_' if name.startswith('usb_reattach_') else 'syscon_target_power_')+name for entry,name in ENTRIES.items()}
DEPENDENCIES={0x3620:('syscon_target_pin_read',1),0x364e:('syscon_target_pin_write',2),0x7f24:('syscon_target_adc_millivolts',1),0x77c0:('syscon_target_timer_delay',1),0x5ad4:('syscon_target_retained_set_battery',1),0x77b4:('syscon_target_now',0),0x7554:('syscon_target_tasks_submit',2),0x8f88:('syscon_target_logger',3),0x2678:('syscon_target_assert',3)}
class AssertionBoundary(Exception):pass
class DependencyBoundary(Exception):pass

def build(out,integrated=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    stub=out/'dependencies.c';stub.write_text('\n'.join('void '+name+'(void){__asm__("bkpt #0");}' for address,(name,_) in DEPENDENCIES.items() if not integrated or address not in (0x7554,0x5ad4)))
    objects=[]
    sources=[ROOT/'src/power/power_state.c',ROOT/'src/power/power_manager_target.c',ROOT/'src/runtime/runtime_memory.c',stub]
    if integrated:sources += [ROOT/'src/scheduling/tasks_target.c',ROOT/'src/power/retained_target.c']
    for i,source in enumerate(sources):
        obj=out/f'{i}.o';objects.append(str(obj))
        toolchain_process.run(['arm-none-eabi-gcc','-std=gnu11','-mcpu=cortex-m0plus','-mthumb','-Os','-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections','-Wall','-Wextra','-Werror','-I'+str(ROOT/'include'),'-c',str(source),'-o',str(obj)],check=True)
    elf=out/'power-manager.elf'
    toolchain_process.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',*objects,'-Wl,-T,'+str(ROOT/'tests/fixtures/target/emulation.ld'),'-Wl,--gc-sections',*(['-Wl,--undefined=syscon_target_tasks_poll','-Wl,--undefined=syscon_target_tasks_init'] if integrated else []),'-Wl,-e,syscon_target_power_measure',*['-Wl,--undefined='+symbol for symbol in SYMBOLS.values()],'-o',str(elf)],check=True)
    return elf

class Pair:
    def __init__(self,elf,integrated=False):
        self.original=Oracle();self.candidate=ArmRebuildOracle(elf);self.machines=(self.original,self.candidate)
        self.power_state=PowerStateComparison(self.original,self.candidate)
        self.envs=[PowerEnvironment(),PowerEnvironment()];self.events=[[],[]];self.on_call=None;self.fail_at=None;self.integrated=integrated
        for index,m in enumerate(self.machines):
            m.cpu.mem_map(0x400b0000,0x1000)
            for address,(name,count) in DEPENDENCIES.items():
                if not integrated or address not in (0x7554,0x5ad4):m.hooks[address if not index else m.symbols[name]&~1]=self.dependency(index,address,count)
            m.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self.memory(index))
    def normalize_value(self,address,size,value):
        for slot in [0x20000534,0x200005a0]:
            for offset,old,name in [(4,0x5149,'usb_assert_callback'),(20,0x50f5,'usb_release_callback')]:
                base=slot+offset
                if base<=address and address+size<=base+4:
                    mask=(1<<(8*size))-1;shift=(address-base)*8
                    candidate=(self.candidate.symbols['syscon_target_power_'+name]>>shift)&mask
                    if value==candidate:return (old>>shift)&mask
        return value
    def memory(self,index):
        def record(uc,kind,address,size,value,_):
            if 0x20000000<=address<0x20000e00 or 0x400b0000<=address<0x400b1000:
                if self.fail_at==len(self.events[index]):raise DependencyBoundary()
                if kind==UC_MEM_READ:value=int.from_bytes(uc.mem_read(address,size),'little')
                value &= (1<<(size*8))-1
                if index:
                    value=self.power_state.word(address,size,value)
                    if self.integrated:value=self.normalize_value(address,size,value)
                self.events[index].append(('memory',kind,address,size,value))
        return record
    def dependency(self,index,address,count):
        def callback(o):
            if self.fail_at==len(self.events[index]):raise DependencyBoundary()
            args=[o.arg(i) for i in range(count)];payload=b''
            if address==0x2678:
                args=[text_argument(o,args[0]),args[1],text_argument(o,args[2])]
                self.events[index].append(('assert',*args));raise AssertionBoundary(*args)
            if address==0x8f88:
                args=list(log_arguments(o,2))
                self.events[index].append(('logger',*args))
                if self.on_call:self.on_call(o,self.envs[index],address,args)
                return 0
            if address==0x7554:
                payload=bytes(o.cpu.mem_read(args[0],args[1]*8));args[0]=0
                if index:
                    for old,name in [(0x5149,'usb_assert_callback'),(0x50f5,'usb_release_callback')]:
                        payload=payload.replace(struct.pack('<I',o.symbols['syscon_target_power_'+name]),struct.pack('<I',old))
            self.events[index].append(('call',address,*args,payload))
            result=self.envs[index].call(address,*(args+[0,0])[:2],payload)
            if address==0x77b4:o.cpu.reg_write(UC_ARM_REG_R1,result>>32)
            if self.on_call:self.on_call(o,self.envs[index],address,args)
            return result
        return callback
    def put(self,address,data):
        for m in self.machines:m.put(address,data)
    def word(self,address,value):self.put(address,struct.pack('<I',value&0xffffffff))
    def execute(self,index,entry,args):
        m=self.machines[index]
        symbol={0x7540:'syscon_target_tasks_init',0x75d8:'syscon_target_tasks_poll'}.get(entry)
        if symbol is None:symbol=SYMBOLS[entry]
        try:
            value=m.call(entry if not index else symbol,*args)
            if entry in (0x7540,0x75d8):value=None
            if entry in (0x4e34,0x4ee0,0x5048):
                value|=m.cpu.reg_read(UC_ARM_REG_R1)<<32
                if index:value=self.power_state.result(value)
            return ('return',value)
        except AssertionBoundary as e:return ('assert',e.args)
        except DependencyBoundary:return ('boundary',)
        except UcError as e:return ('cpu-fault',e.errno)
    def run(self,entry,*args):
        self.events=[[],[]]
        a=self.execute(0,entry,args);b=self.execute(1,entry,args)
        assert a==b,(hex(entry),args,a,b)
        assert self.events[0]==self.events[1],(hex(entry),args,next(((i,x,y) for i,(x,y) in enumerate(zip(*self.events)) if x!=y),None),len(self.events[0]),len(self.events[1]))
        candidate=bytearray(self.power_state.memory(0x20000000,self.candidate.read(0x20000000,0xe00)))
        if self.integrated:
            for offset in range(0xe00):candidate[offset]=self.normalize_value(0x20000000+offset,1,candidate[offset])
        assert bytes(self.original.cpu.mem_read(0x20000000,0xe00))==bytes(candidate)
        assert self.envs[0].gpio==self.envs[1].gpio
        return a
