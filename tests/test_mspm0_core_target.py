"""Direct ARM-vs-ARM core/GPIO ABI, callbacks and ordered bus effects."""
from collections import deque
from pathlib import Path
import random
import struct
import subprocess
import pytest
from unicorn import UC_MEM_READ,UC_MEM_WRITE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_PROT_READ,UC_PROT_EXEC,UcError
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_SP,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11
from arm_rebuild_oracle import ArmRebuildOracle
from oracle import Oracle
ROOT=Path(__file__).resolve().parents[1]
DESCRIPTORS=0x2000016c
HANDLERS=0x20000698
CFG=0x20000800
CALLBACK=0x10080
ENTRIES={0x798c:'watchdog_init',0x79d0:'watchdog_feed',0x7a50:'hal_noop',0x7a54:'gpio_lookup',
  0x7c08:'reset_cause',0x7c3c:'reset_cause_name',0x7f58:'gpio_config',0x8054:'gpio_write',
  0x80ac:'gpio_toggle',0x80f8:'gpio_read',0x8148:'gpio_attach',0x81f8:'gpio_detach',0x8258:'gpio_irq'}
REGIONS=[(0x40080000,0x2000),(0x400a0000,0x2000),(0x400af000,0x2000),
         (0x40401000,0x1000),(0x40428000,0x1000),(0xe000e000,0x1000)]
class AssertReached(Exception):pass
class InjectedFault(Exception):pass

@pytest.fixture(scope='module')
def core_elf(tmp_path_factory):
    out=tmp_path_factory.mktemp('core-target');elf=out/'core.elf'
    trap=out/'assert.c';trap.write_text('void syscon_target_assert(unsigned a,unsigned b,unsigned c){(void)a;(void)b;(void)c;__asm__("bkpt #0");}\n')
    subprocess.run(['arm-none-eabi-gcc','-std=c11','-mcpu=cortex-m0plus','-mthumb','-Os',
        '-ffreestanding','-fno-builtin','-nostdlib','-Wall','-Wextra','-Werror','-I'+str(ROOT/'include'),
        str(ROOT/'target/mspm0_core_target.c'),str(ROOT/'target/gpio_state.c'),str(ROOT/'src/runtime_memory.c'),str(trap),
        '-Wl,-T,'+str(ROOT/'target/emulation.ld'),'-Wl,-e,syscon_target_gpio_config','-o',str(elf)],check=True)
    return elf

class Pair:
    def __init__(self,elf):
        self.original=Oracle();self.original.cpu.mem_protect(0,0x10000,UC_PROT_READ|UC_PROT_EXEC);self.candidate=ArmRebuildOracle(elf)
        self.machines=(self.original,self.candidate);self.events=[[],[]];self.scripts=[{},{}]
        self.fail_at=None;self.assertions=[[],[]]
        for i,m in enumerate(self.machines):
            for base,size in REGIONS:m.cpu.mem_map(base,size)
            if i:m.cpu.mem_map(0x10000,0x1000)
            m.put(CALLBACK,bytes.fromhex('014a10605160704700090020'))
            m.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self.record(i))
            def assertion(o,index=i):
                args=(o.cstring(o.arg(0)),o.arg(1),o.cstring(o.arg(2)));self.assertions[index].append(args)
                raise AssertReached(args)
            address=0x2678 if not i else m.symbols['syscon_target_assert']&~1
            m.hooks[address]=assertion
    def record(self,index):
        def hook(cpu,kind,address,size,value,_):
            if not (0x20000000<=address<0x20000f00 or any(b<=address<b+n for b,n in REGIONS)):return
            if len(self.events[index])==self.fail_at:raise InjectedFault((kind,address,size))
            if kind==UC_MEM_READ:
                script=self.scripts[index].get(address)
                if script:cpu.mem_write(address,script.popleft().to_bytes(size,'little'))
                value=int.from_bytes(cpu.mem_read(address,size),'little')
            self.events[index].append((kind,address,size,value&((1<<(size*8))-1)))
        return hook
    def put(self,address,data):
        for m in self.machines:m.put(address,data)
    def word(self,address,value):self.put(address,struct.pack('<I',value&0xffffffff))
    def script(self,address,values):
        for s in self.scripts:s[address]=deque(values)
    def descriptor(self,pin,physical,mux=0,port=0x400a0000):
        self.put(DESCRIPTORS+pin*8,struct.pack('<IBBH',port,physical,mux,0xa55a))
    def reset_events(self):
        self.events=[[],[]];self.assertions=[[],[]]
    def invoke(self,index,entry,args):
        m=self.machines[index]
        try:
            saved=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
            for i,reg in enumerate(saved):m.cpu.reg_write(reg,0x89ab0000+i*0x123)
            result=m.call(entry if not index else 'syscon_target_'+ENTRIES[entry],*args)
            assert [m.cpu.reg_read(reg) for reg in saved]==[0x89ab0000+i*0x123 for i in range(8)]
            assert m.cpu.reg_read(UC_ARM_REG_SP)==(0x20000ff0 if not index else 0x2100ff00)
            if entry==0x8148:result|=m.cpu.reg_read(UC_ARM_REG_R1)<<32
            if entry==0x7c3c:result=m.cstring(result)
            if entry in (0x7a50,0x8258):result=None
            return ('return',result)
        except AssertReached as e:return ('assert',e.args)
        except InjectedFault as e:return ('bus-fault',e.args)
        except UcError as e:return ('cpu-fault',e.errno)
    def run(self,entry,*args):
        self.reset_events();a=self.invoke(0,entry,args);b=self.invoke(1,entry,args)
        assert a==b,(hex(entry),args,a,b)
        assert self.events[0]==self.events[1],(hex(entry),args,self.events)
        assert bytes(self.original.cpu.mem_read(0x20000000,0xf00))==self.candidate.read(0x20000000,0xf00)
        return a


def test_watchdog_exact_key_write_order_feed_and_noop(core_elf):
    p=Pair(core_elf)
    assert p.run(0x798c)==('return',0)
    assert [e[1:] for e in p.events[0]]==[(0x40080804,4,0xb1000003),(0x40080800,4,0x26000001),
        (0x40081104,4,0xbe000000),(0x40081100,4,0xc9020033),(0x40081108,4,0xa7)]
    assert p.run(0x79d0)==('return',0) and len(p.events[0])==1
    p.run(0x7a50);assert not p.events[0]


def test_gpio_lookup_all_byte_indices_and_full_width_invalids(core_elf):
    p=Pair(core_elf)
    for pin in [*range(256),256,65536,0x7fffffff,0x80000000,0xffffffff]:
        assert p.run(0x7a54,pin)==('return',DESCRIPTORS+8*pin if pin<25 else 0)
        assert not p.events[0]


def test_gpio_reset_names_and_assertions_ignore_original_private_rom(core_elf):
    p=Pair(core_elf)
    p.candidate.put(0xdd7b,b'\xa5'*(0xdfa9-0xdd7b))
    p.candidate.put(0xcceb,b'\xa5'*8)
    for raw in range(32):
        p.put(0x20000254,b'\xff');p.word(0x400b0220,raw)
        p.run(0x7c08)
    for cause in [*range(8),0xffffffff]:p.run(0x7c3c,cause)
    assert p.run(0x7f58,0,0)[0]=='assert'
    assert p.run(0x8054,25,0)[0]=='assert'


def test_reset_cause_cached_byte_domain_mmio_mask_and_name_contents(core_elf):
    p=Pair(core_elf)
    for cached in range(256):
        p.put(0x20000254,bytes([cached]));p.word(0x400b0220,0xffffffff)
        p.run(0x7c08)
        reads=[e for e in p.events[0] if e[1]==0x400b0220]
        assert len(reads)==(1 if cached==255 else 0)
    for raw in [*range(64),0x7fffffff,0x80000000,0xffffffff]:
        p.put(0x20000254,b'\xff');p.word(0x400b0220,raw)
        value=p.run(0x7c08);p.word(0x400b0220,raw^31)
        assert p.run(0x7c08)==value
        assert all(e[1]!=0x400b0220 for e in p.events[0])
    for cause in [*range(256),256,0xffffffff]:p.run(0x7c3c,cause)

@pytest.mark.parametrize('mode',[0,1,2,255])
def test_gpio_config_input_output_other_modes_all_physical_shift_counts(core_elf,mode):
    p=Pair(core_elf);rng=random.Random(mode)
    for physical in range(256):
        pin=physical%25;mux=(physical*7)&255;p.descriptor(pin,physical,mux)
        for pull,value,flags in [(0,0,0),(1,0,2),(2,1,2),(3,255,0xffffffff)]:
            cfg=bytearray(rng.randbytes(12));cfg[4:8]=bytes([mode,pull,0,value]);struct.pack_into('<I',cfg,8,flags)
            p.put(CFG,cfg);p.run(0x7f58,pin,CFG)


def test_gpio_config_full_mode_pull_and_initial_value_byte_domains(core_elf):
    p=Pair(core_elf);p.descriptor(0,7,8)
    for byte in range(256):
        for mode,pull,value,flags in [(byte,0,0,0),(0,byte,0,0),(1,0,byte,2)]:
            cfg=bytearray(12);cfg[4:8]=bytes([mode,pull,0,value]);struct.pack_into('<I',cfg,8,flags)
            p.put(CFG,cfg);p.run(0x7f58,0,CFG)


def test_gpio_read_write_toggle_all_physical_byte_values_and_boolean_arguments(core_elf):
    p=Pair(core_elf);rng=random.Random(0x80f8)
    for physical in range(256):
        pin=physical%25;p.descriptor(pin,physical)
        for value in [0,1,255,0x80000000,0xffffffff]:p.run(0x8054,pin,value)
        p.run(0x80ac,pin)
        for value in [0,0xffffffff,rng.getrandbits(32)]:
            p.word(0x400a1380,value);p.run(0x80f8,pin)


def test_irq_attach_detach_full_shift_byte_domain_and_edge_normalization(core_elf):
    p=Pair(core_elf);rng=random.Random(0x8148)
    for physical in range(256):
        pin=physical%25;p.descriptor(pin,physical)
        for edge in [0,1,2,3,255,0x80000000,0xffffffff]:
            for offset in [0x1390,0x13a0,0x1048,0x1028]:p.word(0x400a0000+offset,rng.getrandbits(32))
            assert p.run(0x8148,pin,edge,CALLBACK|1,0x12340000+physical)==('return',pin<<32)
            assert p.run(0x81f8,pin)==('return',0)


def test_gpio_attach_rereads_polarity_and_unusual_writeonly_clear_register(core_elf):
    p=Pair(core_elf);p.descriptor(5,17)
    p.script(0x400a13a0,[0xa5a5a5a5,0xf0f0f0f0]);p.script(0x400a1048,[0x01234567])
    p.script(0x400a1028,[0x89abcdef]);p.run(0x8148,5,2,CALLBACK|1,8)
    writes=[e for e in p.events[0] if e[0]==UC_MEM_WRITE]
    assert (UC_MEM_WRITE,0x400a13a0,4,0xf0f0f0f0|8) in writes
    assert (UC_MEM_WRITE,0x400a1048,4,0x01234567|(1<<17)) in writes

@pytest.mark.parametrize('entry,line',[(0x7f58,0x22),(0x8054,0x61),(0x80ac,0x6d),(0x80f8,0x74),(0x8148,0x7a),(0x81f8,0x9b)])
def test_invalid_pin_asserts_before_gpio_access_with_exact_file_line_expression(core_elf,entry,line):
    p=Pair(core_elf)
    for pin in [25,26,255,256,0x80000000,0xffffffff]:
        args=[pin,CFG,123,456] if entry==0x7f58 else [pin,1,CALLBACK|1,789]
        result=p.run(entry,*args)
        assert result[0]=='assert'
        assert p.assertions[0]==p.assertions[1]
        file,observed_line,expression=p.assertions[0][0]
        assert file==b'hal_gpio.cpp' and observed_line==line
        assert expression==b'pin < HAL_PLATFORM_PIN_NUM'
        assert not p.events[0]
    if entry==0x7f58:
        for pin in [0,25,0xffffffff]:
            assert p.run(entry,pin,0)[0]=='assert'
            assert p.assertions[0][0][1:]==(0x21,b'config != nullptr')


def test_gpio_irq_real_callback_dispatch_full_scan_and_first_match_precedence(core_elf):
    p=Pair(core_elf)
    for pin in range(25):
        p.descriptor(pin,pin);p.word(HANDLERS+8*pin,CALLBACK|1);p.word(HANDLERS+8*pin+4,0x12340000+pin)
    for reason in [0,1,2,25,26,256,257,0xffffffff]:
        p.put(0x20000900,b'\xff'*8);p.word(0x40401130,1);p.word(0x400a1020,reason)
        p.run(0x8258)
        expected=(reason-1)&255
        result=struct.unpack('<II',p.candidate.read(0x20000900,8))
        assert result==((expected,0x12340000+expected) if expected<25 else (0xffffffff,0xffffffff))
    # First descriptor match with a null handler stops, even if a later match is callable.
    p.descriptor(0,7);p.descriptor(1,7);p.word(HANDLERS,0);p.word(0x400a1020,8)
    p.put(0x20000900,b'\xff'*8);p.run(0x8258)
    assert p.candidate.read(0x20000900,8)==b'\xff'*8
    for group in [0,2,0xffffffff]:
        p.word(0x40401130,group);p.run(0x8258)
        assert len(p.events[0])==1


def test_gpio_irq_nonmatching_port_skips_pin_read_and_attach_irq_detach_flow(core_elf):
    p=Pair(core_elf)
    for pin in range(25):p.descriptor(pin,pin,port=0x400b0000)
    p.descriptor(24,31);p.word(0x40401130,1);p.word(0x400a1020,32)
    p.run(0x8148,24,3,CALLBACK|1,0xfedcba98)
    p.run(0x8258);assert p.candidate.read(0x20000900,8)==struct.pack('<II',24,0xfedcba98)
    assert not any(e[1]==DESCRIPTORS+8*i+4 for e in p.events[0] for i in range(24))
    p.run(0x81f8,24);p.put(0x20000900,b'\0'*8);p.run(0x8258)
    assert p.candidate.read(0x20000900,8)==b'\0'*8

@pytest.mark.parametrize('entry,args',[(0x7f58,(2,CFG)),(0x8054,(2,1)),(0x80ac,(2,)),(0x80f8,(2,)),(0x8148,(2,1,CALLBACK|1,8)),(0x81f8,(2,))])
def test_gpio_fault_at_each_access_preserves_ordered_prefix(core_elf,entry,args):
    def prepare():
        p=Pair(core_elf);p.descriptor(2,8,9);p.put(CFG,bytes(12));return p
    p=prepare();p.run(entry,*args)
    for position in range(len(p.events[0])):
        q=prepare();q.fail_at=position
        assert q.run(entry,*args)[0]=='bus-fault'
        assert len(q.events[0])==position


def test_config_pointer_fault_is_after_power_write_and_before_gpio_mode_side_effect(core_elf):
    p=Pair(core_elf);p.descriptor(3,4,5)
    assert p.run(0x7f58,3,0x30000000)[0]=='cpu-fault'
    assert [e for e in p.events[0] if e[0]==UC_MEM_WRITE]==[(UC_MEM_WRITE,0x400a0800,4,0x26000001)]


def test_gpio_config_aliases_descriptor_and_power_write_changes_later_mux_read(core_elf):
    p=Pair(core_elf);pin=4;descriptor=DESCRIPTORS+pin*8
    # PWREN overwrites the descriptor's physical/mux bytes after physical was
    # captured, before mux is read. Both implementations must observe that order.
    p.descriptor(pin,7,91,port=descriptor+4-0x800)
    p.put(CFG,bytes(12));p.run(0x7f58,pin,CFG)
    writes=[e for e in p.events[0] if e[0]==UC_MEM_WRITE]
    assert (UC_MEM_WRITE,descriptor+4,4,0x26000001) in writes
    assert any(e[1]==0x40428004 for e in writes)
    # Configuration byte mode itself is also allowed to alias the power write.
    p=Pair(core_elf);p.descriptor(3,5,6);config=0x400a0800-4
    p.put(config,bytes(12));p.run(0x7f58,3,config)
    assert (UC_MEM_WRITE,0x400a12d0,4,1<<5) in p.events[0]
    assert not any(e[1]==0x400a12e0 for e in p.events[0])


def test_gpio_read_loads_pin_byte_after_mmio_read_and_attach_reads_port_after_handler_writes(core_elf):
    p=Pair(core_elf);pin=6;descriptor=DESCRIPTORS+pin*8
    p.descriptor(pin,9);p.script(descriptor+4,[31]);p.word(0x400a1380,0x80000000)
    assert p.run(0x80f8,pin)==('return',1)
    # Ordering is asserted explicitly in addition to matching reference traces.
    addresses=[e[1] for e in p.events[0]]
    assert addresses.index(0x400a1380)<addresses.index(descriptor+4)
    p=Pair(core_elf);p.descriptor(pin,9);p.run(0x8148,pin,2,CALLBACK|1,55)
    addresses=[e[1] for e in p.events[0]]
    assert addresses.index(HANDLERS+pin*8+4)<addresses.index(descriptor)


def test_invalid_callback_and_unmapped_port_fault_without_synthetic_success(core_elf):
    for callback in [0x30000001,CALLBACK]:
        p=Pair(core_elf)
        p.descriptor(0,4);p.word(HANDLERS,callback);p.word(HANDLERS+4,0x1234)
        p.word(0x40401130,1);p.word(0x400a1020,5)
        assert p.run(0x8258)[0]=='cpu-fault'
    for entry,args in [(0x7f58,(0,CFG)),(0x8054,(0,1)),(0x80ac,(0,)),(0x80f8,(0,))]:
        p=Pair(core_elf);p.descriptor(0,4,port=0x30000000);p.put(CFG,bytes(12))
        assert p.run(entry,*args)[0]=='cpu-fault'


def test_assert_basename_no_separator_and_noop_preserves_incoming_r0(core_elf):
    p=Pair(core_elf);p.put(0xdf49,b'hal_gpio.cpp\0')
    assert p.run(0x8054,25,0)[0]=='assert'
    assert p.assertions[0][0]==(b'hal_gpio.cpp',0x61,b'pin < HAL_PLATFORM_PIN_NUM')
    for value in [0,1,0x80000000,0xffffffff]:
        p.run(0x7a50,value)
        assert all(m.cpu.reg_read(UC_ARM_REG_R0)==value for m in p.machines)


def test_gpio_output_flags_every_bit_and_flash_write_fault(core_elf):
    p=Pair(core_elf);p.descriptor(2,9,10)
    for inverted in [0,0xffffffff]:
        for bit in range(32):
            flags=(1<<bit)^inverted
            config=bytearray(12);config[4]=1;config[7]=255;struct.pack_into('<I',config,8,flags)
            p.put(CFG,config);p.run(0x7f58,2,CFG)
            writes=[e for e in p.events[0] if e[0]==UC_MEM_WRITE and e[1]==0x400a1290]
            assert len(writes)==bool(flags&2)
    p=Pair(core_elf);p.descriptor(0,0,port=0);p.put(CFG,bytes(12))
    assert p.run(0x7f58,0,CFG)[0]=='cpu-fault'
