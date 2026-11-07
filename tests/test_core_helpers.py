import json
import random
import struct
import subprocess
from pathlib import Path
import pytest
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_MEM_READ
from unicorn.arm_const import UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_SP,UC_ARM_REG_R0,UC_ARM_REG_R3,UC_ARM_REG_PRIMASK,UC_ARM_REG_APSR
from oracle import Oracle
ROOT=Path(__file__).resolve().parents[1]
CODE=0x01000000
LOGGER=0x10040

@pytest.fixture(scope='module')
def helpers(tmp_path_factory):
    root=tmp_path_factory.mktemp('core-helpers-arm');obj=root/'helpers.o';elf=root/'helpers.elf';binary=root/'helpers.bin'
    flags=['-std=c11','-Wall','-Wextra','-Werror','-mcpu=cortex-m0plus','-mthumb','-Os','-ffreestanding','-fno-unwind-tables','-fno-asynchronous-unwind-tables']
    subprocess.run(['arm-none-eabi-gcc',*flags,'-c',str(ROOT/'target/core_helpers.c'),'-o',str(obj)],check=True)
    subprocess.run(['arm-none-eabi-ld','-e','syscon_mcu_sleep','-Ttext=0x01000000','--defsym=syscon_core_log=0x10041',str(obj),'-o',str(elf)],check=True)
    subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(elf),str(binary)],check=True)
    symbols={}
    for line in subprocess.check_output(['arm-none-eabi-nm','-S',str(elf)],text=True).splitlines():
        fields=line.split()
        if len(fields)==4:symbols[fields[3]]=(int(fields[0],16),int(fields[1],16))
    return binary.read_bytes(),symbols,flags

class SleepOracle(Oracle):
    def __init__(self,initial,wake,mask,helpers=None):
        super().__init__();self.events=[];self.value=initial;self.wake=wake
        self.cpu.mem_map(0xe000e000,0x1000)
        self.cpu.reg_write(UC_ARM_REG_PRIMASK,mask)
        self.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self.mmio,begin=0xe000e010,end=0xe000e013)
        self.cpu.hook_add(UC_HOOK_CODE,self.instructions)
        self.hooks[0x8f88]=self.log;self.hooks[LOGGER]=self.log
        if helpers:
            self.cpu.mem_map(CODE,0x1000);self.put(CODE,helpers[0])
    def log(self,o):self.events.append(('log',o.arg(0),o.cstring(o.arg(1)),o.cstring(o.arg(2)),self.cpu.reg_read(UC_ARM_REG_PRIMASK)))
    def mmio(self,uc,kind,address,size,value,_):
        assert address==0xe000e010 and size==4
        if kind==UC_MEM_READ:
            self.put(address,struct.pack('<I',self.value));self.events.append(('read',self.value,uc.reg_read(UC_ARM_REG_PRIMASK)))
        else:self.value=value;self.events.append(('write',value,uc.reg_read(UC_ARM_REG_PRIMASK)))
    def instructions(self,uc,address,size,_):
        code=bytes(uc.mem_read(address,size))
        names={b'\x72\xb6':'disable',b'\x62\xb6':'enable',b'\xbf\xf3\x4f\x8f':'dsb',b'\xbf\xf3\x6f\x8f':'isb',b'\x30\xbf':'wfi'}
        if code in names:
            self.events.append((names[code],))
            if names[code]=='wfi':
                # Explicit immediate wake: no physical sleep/interrupt timing model.
                self.events.append(('wake-register-change',self.wake));self.value=self.wake
                uc.reg_write(UC_ARM_REG_PC,(address+2)|1)

def test_sleep_matches_original_irq_barriers_register_reread_and_logs(helpers):
    rng=random.Random(0x74f8)
    for mask in [0,1]:
        for initial,wake in [(0,0),(2,0),(0xffffffff,0x80000000),*[(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(20)]]:
            original=SleepOracle(initial,wake,mask);candidate=SleepOracle(initial,wake,mask,helpers)
            original.call(0x74f8);candidate.call(helpers[1]['syscon_mcu_sleep'][0])
            assert candidate.events==original.events
            assert candidate.value==original.value
            assert candidate.cpu.reg_read(UC_ARM_REG_PRIMASK)==original.cpu.reg_read(UC_ARM_REG_PRIMASK)==0

def delay_oracle(helpers,cycles,candidate,budget=None):
    o=Oracle();entry=0x7ae8
    if candidate:
        o.cpu.mem_map(CODE,0x1000);o.put(CODE,helpers[0]);entry=helpers[1]['syscon_cycle_delay'][0]
    trace=[]
    o.cpu.hook_add(UC_HOOK_CODE,lambda uc,a,size,_:trace.append(a-entry))
    o.cpu.reg_write(UC_ARM_REG_SP,0x20000ff0);o.cpu.reg_write(UC_ARM_REG_LR,o.SENTINEL|1);o.cpu.reg_write(UC_ARM_REG_R0,cycles)
    o.cpu.emu_start(entry|1,o.SENTINEL,count=budget or 200000)
    return trace,o.cpu.reg_read(UC_ARM_REG_PC)==o.SENTINEL,o.cpu.reg_read(UC_ARM_REG_R3),o.cpu.reg_read(UC_ARM_REG_APSR)

def test_cycle_delay_exact_bytes_and_completed_instruction_traces(helpers):
    image,symbols,flags=helpers;start,size=symbols['syscon_cycle_delay'];candidate=image[start-CODE:start-CODE+size]
    original=Oracle().image[0x7ae8:0x7af2]
    assert candidate==original
    for cycles in [*range(2,130),255,256,257,1000,3200,32000]:
        a=delay_oracle(helpers,cycles,False);b=delay_oracle(helpers,cycles,True)
        assert a==b
        assert a[1]
        assert len(a[0])==2+3*((cycles-2)//4+1)
    (ROOT/'analysis/core-helper-binary-comparison.json').write_text(json.dumps(dict(
        function='syscon_cycle_delay',original_address='0x7ae8',original_size=10,reconstructed_size=size,
        exact_bytes=True,compiler=subprocess.check_output(['arm-none-eabi-gcc','--version'],text=True).splitlines()[0],
        compiler_flags=flags,whole_firmware_match=False,physical_timing_verified=False,flash_candidate=False),indent=2)+'\n')

def test_cycle_delay_underflow_and_large_inputs_do_not_falsely_return(helpers):
    for cycles in [0,1,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]:
        a=delay_oracle(helpers,cycles,False,300);b=delay_oracle(helpers,cycles,True,300)
        assert a==b
        assert not a[1]
