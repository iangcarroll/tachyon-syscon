"""Original-ABI diagnostics: real arithmetic, parsing and bounded formatting."""
import random
import struct
import subprocess
from pathlib import Path
import pytest
from unicorn import UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE, UC_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R1
from oracle import Oracle
from arm_rebuild_oracle import ArmRebuildOracle
from power_state_comparison import log_arguments
import build_runtime_scan_image as runtime
ROOT=Path(__file__).resolve().parents[1]
GETTERS=[(0x3114,'auto_boot'),(0x3120,'wakeup_enabled'),(0x312c,'log_color'),
         (0x3138,'alt_powerkey'),(0x3144,'factory_test'),(0x3150,'modem_always_on')]

@pytest.fixture(scope='module')
def diagnostic_elf(tmp_path_factory):
    directory=tmp_path_factory.mktemp('diagnostics')
    stub=directory/'dependencies.S'
    names=['power_measure','gpio_read','adc_temperature','modem_off','power_minimum']
    stub.write_text('.syntax unified\n.thumb\n'+''.join(
        f'.global syscon_target_{name}\n.type syscon_target_{name},%function\n.thumb_func\nsyscon_target_{name}:\n bkpt #0\n bx lr\n' for name in names))
    old=runtime.SOURCES
    try:
        runtime.SOURCES=old+['target/app/diagnostics_target.c','target/app/diagnostics_state.c','src/format.c','src/logging.c',
                            'target/testing/format_wrappers.c','target/logging/logger_target.c','target/logging/logger_state.c','target/logging/logger_target_abi.S',str(stub)]
        return runtime.build(directory)
    finally:runtime.SOURCES=old

class Pair:
    def __init__(self,elf):
        self.machines=[Oracle(),ArmRebuildOracle(elf)];self.events=[[],[]]
    def put(self,address,data):
        for cpu in self.machines:cpu.put(address,data)
    def bind(self,address,name,fn):
        for i,cpu in enumerate(self.machines):
            entry=address if i==0 else cpu.symbols['syscon_target_'+name]&~1
            cpu.hooks[entry]=lambda machine,i=i:fn(machine,self.events[i],i)
    def call(self,address,name,*args,void=False):
        self.events=[[],[]]
        a=self.machines[0].call(address,*args,count=1000000)
        b=self.machines[1].call('syscon_target_'+name,*args,count=1000000)
        if not void:assert a==b,(hex(address),a,b)
        assert self.events[0]==self.events[1],self.events
        return a
    def equal(self,address,size):
        assert bytes(self.machines[0].cpu.mem_read(address,size))==self.machines[1].read(address,size)


def test_configuration_getters_preserve_full_byte_and_enable_truncation(diagnostic_elf):
    p=Pair(diagnostic_elf)
    for value in range(256):
        p.put(0x20000030,bytes([value])*6)
        for address,name in GETTERS:assert p.call(address,name)==value
        p.call(0x347c,'diagnostics_enable',value|0xabcdef00,void=True)
        p.equal(0x20000046,1)
        assert p.machines[0].cpu.mem_read(0x20000046,1)==bytes([value])


def test_packed_fields_read_order_and_live_mutation(diagnostic_elf):
    p=Pair(diagnostic_elf);traces=[[],[]];rng=random.Random(0x315c)
    for i,cpu in enumerate(p.machines):
        def observe(uc,kind,address,size,value,_,i=i):
            traces[i].append((address,size))
            # A concurrently changing byte makes reordered loads observable.
            uc.mem_write(0x20000036,bytes([(len(traces[i])*31)&255]))
        cpu.cpu.hook_add(UC_HOOK_MEM_READ,observe,begin=0x20000036,end=0x2000003d)
    for _ in range(100):
        p.put(0x20000036,rng.randbytes(8))
        for address,name in [(0x315c,'powerkey_long_seconds'),(0x3178,'powerkey_extra_seconds')]:
            traces[0].clear();traces[1].clear();p.call(address,name)
            assert traces[0]==traces[1]


def test_revision_uses_complete_source_backed_scan_parser(diagnostic_elf):
    p=Pair(diagnostic_elf)
    values=[b'',b'v1.2',b'v1.2.0',b'v1.1.9',b'v2.9.0',b'v1.-1.0',b'v1.4294967295.0',
            b'v1.4294967296.0',b'v1.+2.0tail',b'v 1.2.0',b'v01.002.0',b'v1.2.',b'1.2.0',
            b'v1.2.999999999999999999999999',b'v2147483648.2.0']
    for value in values:
        p.put(0x2000003e,value+b'\0');p.call(0x3194,'hwrevision_new')
    assert not p.machines[0].hook_calls and not p.machines[1].hook_calls


def configure_poll(p,clocks,temperature,off=0,wake=0):
    indices=[0,0]
    def now(cpu,events,i):
        index=indices[i];indices[i]+=1;events.append(('now',index))
        cpu.cpu.reg_write(UC_ARM_REG_R1,clocks[index]>>32);return clocks[index]
    p.bind(0x77b4,'now',now)
    def measure(cpu,events,i):
        pin=cpu.arg(0);events.append(('measure',pin));return (pin*0x1234567)&0xffffffff
    p.bind(0x4c50,'power_measure',measure)
    for addr,name,result in [(0x80f8,'gpio_read',wake),(0x7d54,'adc_temperature',temperature),
                             (0x6690,'modem_off',off),(0x55c4,'power_minimum',0x87654321)]:
        def invoke(cpu,events,i,name=name,result=result):
            events.append((name,cpu.arg(0)) if name=='gpio_read' else (name,));return result
        p.bind(addr,name,invoke)
    def log(cpu,events,i):
        events.append(('log',log_arguments(cpu,2)));return 0
    p.bind(0x8f88,'logger',log)
    return indices


def test_poll_clock_boundaries_counter_wrap_and_disabled_logging(diagnostic_elf):
    p=Pair(diagnostic_elf)
    for now in [0,4999,5000,5001,0xffffffff,0x100000000,0xffffffffffffffff]:
        for previous in [0,1,5000,0xffffffff]:
            for loops in [0,0xffffffff,0xffffffffffffffff]:
                p.put(0x200002c0,struct.pack('<QII',loops,previous,previous))
                p.put(0x20000046,b'\0');configure_poll(p,[now,now,now],0)
                p.call(0x3488,'diagnostics_poll',void=True);p.equal(0x200002c0,16)


def test_poll_log_arguments_temperature_truncation_and_zero_division(diagnostic_elf):
    p=Pair(diagnostic_elf);rng=random.Random(0x3488)
    temperatures=[0x80000000,-2147483647,-12345,-10,-9,-1,0,1,9,10,12345,2147483647]
    for temperature in temperatures:
        for previous in [0,6000,6001,6002,0xffffffff]:
            loops=rng.getrandbits(64);off=rng.getrandbits(32);wake=rng.choice([0,1,0xffffffff])
            p.put(0x200002c0,struct.pack('<QII',loops,0,previous));p.put(0x20000046,b'\xff')
            indices=configure_poll(p,[6001,6001,0x123456789],temperature,off,wake)
            p.call(0x3488,'diagnostics_poll',void=True);p.equal(0x200002c0,16)
            assert indices==[3,3]
            assert len([x for x in p.events[0] if x[0]=='log'])==2


def test_poll_persistent_memory_access_width_order_and_mutation(diagnostic_elf):
    p=Pair(diagnostic_elf);traces=[[],[]]
    for i,cpu in enumerate(p.machines):
        def record(uc,kind,address,size,value,_,i=i):
            if kind!=UC_MEM_WRITE:value=int.from_bytes(uc.mem_read(address,size),'little')
            traces[i].append((kind,address,size,value&((1<<(8*size))-1)))
            # Mutation after the first low-word load exposes read64 ordering.
            if len(traces[i])==1:uc.mem_write(0x200002c4,struct.pack('<I',0xffffffff))
        cpu.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,record,begin=0x200002c0,end=0x200002cf)
    for enable in [0,1]:
        p.put(0x200002c0,struct.pack('<QII',0xffffffff,0,0));p.put(0x20000046,bytes([enable]))
        traces[0].clear();traces[1].clear();configure_poll(p,[6001]*3,0)
        p.call(0x3488,'diagnostics_poll',void=True);assert traces[0]==traces[1]


def test_diagnostic_text_does_not_read_original_rom(diagnostic_elf):
    p=Pair(diagnostic_elf)
    for address,size in [(0xb24c,0x7d),(0xcb73,3),(0xd9ea,7),(0xcd10,5),(0xcd1d,4)]:
        p.machines[1].put(address,b'\xa5'*size)
    for temperature in [0x80000000,-1,123,0]:
        p.put(0x200002c0,struct.pack('<QII',73,0,0))
        p.put(0x20000046,b'\1')
        configure_poll(p,[6001]*3,temperature,wake=1)
        p.call(0x3488,'diagnostics_poll',void=True)
