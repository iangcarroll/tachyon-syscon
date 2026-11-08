"""Direct target assertion and breadcrumbs, including post-reset-request wait."""
from collections import deque
from pathlib import Path
import random
import struct
import subprocess
import capstone
import pytest
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_READ,UC_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_PRIMASK
from arm_rebuild_oracle import ArmRebuildOracle
from oracle import Oracle
ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def fault_target_elf(tmp_path_factory):
    out=tmp_path_factory.mktemp('fault-control-target');elf=out/'test.elf'
    trap=out/'traps.c'
    names=['syscon_target_logger','syscon_target_gpio_config','syscon_target_gpio_toggle',
        'syscon_target_gpio_read','syscon_target_watchdog_feed','syscon_cycle_delay']
    trap.write_text('\n'.join('void '+n+'(void){__asm__("bkpt #0");}' for n in names)+'\n')
    subprocess.run(['arm-none-eabi-gcc','-std=c11','-Os','-mcpu=cortex-m0plus','-mthumb','-ffreestanding','-fno-builtin',
        '-nostdlib','-Wall','-Wextra','-Werror','-I',str(ROOT/'include'),str(ROOT/'target/fault_control_target.c'),
        str(ROOT/'target/gpio_state.c'),str(ROOT/'src/runtime_memory.c'),str(trap),'-Wl,-T,'+str(ROOT/'target/emulation.ld'),
        '-Wl,-e,syscon_target_assert','-o',str(elf)],check=True)
    return elf

class Pair:
    def __init__(self,elf,buttons=()):
        self.o=Oracle();self.a=ArmRebuildOracle(elf);self.events=[[],[]];self.buttons=[deque(buttons),deque(buttons)]
        decoder=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_THUMB)
        for index,machine in enumerate((self.o,self.a)):
            machine.cpu.mem_map(0xe000e000,4096);machine.cpu.mem_map(0x400b0000,4096)
            def memory(uc,kind,address,size,value,_,i=index):
                if address not in (0xe000e010,0xe000ed0c,0x400b040c,0x400b0104):return
                self.events[i].append(('write' if kind==UC_MEM_WRITE else 'read',address,
                    value if kind==UC_MEM_WRITE else int.from_bytes(uc.mem_read(address,size),'little')))
            machine.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,memory)
            def instruction(uc,address,size,_,i=index):
                raw=bytes(uc.mem_read(address,size))
                if raw not in (b'\x72\xb6',b'\xbf\xf3\x4f\x8f'):return
                ins=next(decoder.disasm(raw,address))
                self.events[i].append(('instruction',ins.mnemonic,ins.op_str))
            machine.cpu.hook_add(UC_HOOK_CODE,instruction)
            def logger(cpu,i=index):
                args=(cpu.arg(0),cpu.cstring(cpu.arg(1)),cpu.cstring(cpu.arg(2)),*(cpu.arg(n) for n in range(3,7)))
                self.events[i].append(('log',args));return 0
            def config(cpu,i=index):self.events[i].append(('config',cpu.arg(0),bytes(cpu.cpu.mem_read(cpu.arg(1),12))));return 0
            def toggle(cpu,i=index):self.events[i].append(('toggle',cpu.arg(0)));return 0
            def delay(cpu,i=index):self.events[i].append(('delay',cpu.arg(0)));return 0
            def feed(cpu,i=index):self.events[i].append(('feed',));return 0
            def button(cpu,i=index):
                value=self.buttons[i].popleft() if self.buttons[i] else 1
                self.events[i].append(('button',cpu.arg(0),value));return value&0xffffffff
            for original,name,callback in [(0x8f88,'syscon_target_logger',logger),(0x7f58,'syscon_target_gpio_config',config),
                (0x80ac,'syscon_target_gpio_toggle',toggle),(0x7ae8,'syscon_cycle_delay',delay),
                (0x79d0,'syscon_target_watchdog_feed',feed),(0x80f8,'syscon_target_gpio_read',button)]:
                machine.hooks[original if index==0 else self.a.symbols[name]&~1]=callback
    def put(self,address,data):
        for machine in (self.o,self.a):machine.put(address,data)

@pytest.mark.parametrize('buttons',[[],[0,0],[0,1]*20,[1]*19+[0,0],[1]*19+[0,1],[2,-1,1,0,1,0,0]])
def test_original_abi_assertion_order_primask_both_barriers_and_nonreturning_wait(fault_target_elf,buttons):
    p=Pair(fault_target_elf,buttons);p.put(0xe000e010,struct.pack('<I',0xffffffff))
    for machine,entry in ((p.o,0x2678),(p.a,'syscon_target_assert')):
        with pytest.raises(RuntimeError,match='budget exhausted'):machine.call(entry,0x20000900,0x12345678,0x20000940,count=5000)
        assert machine.cpu.reg_read(UC_ARM_REG_PRIMASK)==1
        assert machine.u32(0xe000ed0c)==0x05fa0004
    assert p.events[0]==p.events[1]
    assert p.events[0][-2:]==[('write',0xe000ed0c,0x05fa0004),('instruction','dsb','sy')]
    assert sum(e[0]=='config' for e in p.events[0])==3
    assert sum(e[0]=='instruction' and e[1]=='dsb' for e in p.events[0])==2


def test_target_breadcrumbs_live_words_cached_bytes_pointer_identity_and_clock_masks(fault_target_elf):
    p=Pair(fault_target_elf);rng=random.Random(0x7b78)
    for value in [*range(24),255,256,0xffffffff]+[rng.getrandbits(32) for _ in range(200)]:
        p.o.call(0x7b78,value);p.a.call('syscon_target_fault_stage_set',value)
        assert p.o.call(0x7b88)==p.a.call('syscon_target_fault_stage_get')==value&255
        assert p.o.cstring(p.o.call(0x7b9c,value))==p.a.cstring(p.a.call('syscon_target_fault_stage_name',value))
        p.put(0x400b0104,struct.pack('<I',value))
        assert p.o.call(0x7be0)==p.a.call('syscon_target_enable_mftick')==0
        assert p.o.u32(0x400b0104)==p.a.u32(0x400b0104)==value|0x1000
        assert p.events[0]==p.events[1]
    for value in range(256):
        p.put(0x20000254,bytes([value]));assert p.o.call(0x7bfc)==p.a.call('syscon_target_cached_reason')==value


def test_fault_diagnostics_ignore_original_private_rom(fault_target_elf):
    p=Pair(fault_target_elf)
    p.a.put(0xacc0,b'\xa5'*(0xacfa-0xacc0))
    p.a.put(0xdd7b,b'\xa5'*(0xde7b-0xdd7b))
    for stage in range(23):
        assert p.o.cstring(p.o.call(0x7b9c,stage))==p.a.cstring(p.a.call('syscon_target_fault_stage_name',stage))
    for machine,entry in [(p.o,0x2678),(p.a,'syscon_target_assert')]:
        with pytest.raises(RuntimeError,match='budget exhausted'):
            machine.call(entry,0x20000900,17,0x20000940,count=5000)
    assert p.events[0]==p.events[1]
