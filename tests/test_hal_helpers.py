"""Actual original ARM bodies versus independently compiled C, no function hooks."""
from collections import deque
import random
import struct
import subprocess
from pathlib import Path
from elftools.elf.elffile import ELFFile
import pytest
from unicorn import Uc,UC_ARCH_ARM,UC_MODE_THUMB,UC_MODE_MCLASS,UC_HOOK_CODE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_READ,UcError
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_SP,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_CPU_ARM_CORTEX_M0
from oracle import Oracle
from inventory import load_image
ROOT=Path(__file__).resolve().parents[1]
CODE=0x01000000
CFG=0x20000800
DATA=0x21000000
BASE=0x41000000
ENTRIES={0x7a68:'syscon_hal_adc_lookup',0x7a90:'syscon_hal_pwm_lookup',
    0x7ac0:'syscon_hal_uart_lookup',0x7ad4:'syscon_hal_i2c_lookup',
    0x930c:'syscon_hal_adc_clock',0x934c:'syscon_hal_i2c_clock',
    0x9374:'syscon_hal_i2c_fill_tx',0x93a0:'syscon_hal_i2c_flush_tx',
    0x93d0:'syscon_hal_i2c_flush_rx',0x964c:'syscon_hal_uart_put_blocking',
    0x9664:'syscon_hal_vref_config',0x9688:'syscon_hal_vref_clock'}

@pytest.fixture(scope='module')
def compiled(tmp_path_factory):
    directory=tmp_path_factory.mktemp('hal-helpers');obj=directory/'helpers.o';elf=directory/'helpers.elf'
    subprocess.run(['arm-none-eabi-gcc','-std=c11','-mcpu=cortex-m0plus','-mthumb','-Os','-ffreestanding','-fno-builtin','-Wall','-Wextra','-Werror','-I'+str(ROOT/'include'),'-c',str(ROOT/'target/hal_helpers.c'),'-o',str(obj)],check=True)
    subprocess.run(['arm-none-eabi-ld','-e','syscon_hal_adc_lookup','-T',str(ROOT/'target/emulation.ld'),str(obj),'-o',str(elf)],check=True)
    symbols={}
    for line in subprocess.check_output(['arm-none-eabi-nm',str(elf)],text=True).splitlines():
        fields=line.split()
        if len(fields)==3:symbols[fields[2]]=int(fields[0],16)
    return elf,symbols

class AccessFault(Exception):pass

class HalOracle(Oracle):
    def __init__(self,compiled=None):
        # Unicorn requires CPU selection before the first memory-map operation.
        self.image=load_image();self.cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS)
        self.cpu.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M0)
        self.cpu.mem_map(0,0x11000);self.put(0,self.image+b'\xff'*(0x10000-len(self.image)))
        self.cpu.mem_map(0x20000000,0x1000)
        self.put(0x20000000,self.image[0xaaf0:0xab20]);self.put(0x20000030,self.image[0xe2e8:0xe578])
        self.hooks={};self.executed=set();self.hook_calls={}
        self.cpu.hook_add(UC_HOOK_CODE,self._step)
        self.compiled=compiled;self.events=[];self.values={};self.scripts={}
        self.fail_at=None;self.stop_after=None;self.control_change=None
        self.cpu.mem_map(BASE,0x2000);self.cpu.mem_map(DATA,0x20000)
        if compiled:
            self.cpu.mem_map(CODE,0x80000)
            with compiled[0].open('rb') as stream:
                for segment in ELFFile(stream).iter_segments():
                    if segment['p_type']!='PT_LOAD' or not segment['p_filesz']:continue
                    address=segment['p_vaddr'];size=segment['p_memsz']
                    assert ((CODE<=address and address+size<=CODE+0x80000) or
                            (any((address,size)==block for block in [(0x200000f4,72),(0x20000148,36),(0x2000013c,12),(0x20000234,32)]) and not segment['p_flags']&1))
                    self.put(address,segment.data())
        for low,high in [(BASE,BASE+0x1fff),(CFG,CFG+63),(DATA,DATA+0x1ffff),
                         (0x200000f4,0x20000263)]:
            self.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self.memory,begin=low,end=high)
    def memory(self,uc,kind,address,size,value,_):
        if self.stop_after is not None and len(self.events)>=self.stop_after:
            raise AccessFault(('event-budget',address,size))
        if len(self.events)==self.fail_at:raise AccessFault(('injected-bus-fault',address,size,kind))
        if kind==UC_MEM_READ:
            if BASE<=address<BASE+0x2000:
                if address not in self.values:raise AccessFault(('unprovided-mmio',address,size))
                script=self.scripts.get(address)
                if script:self.values[address]=script.popleft()
                value=self.values[address]&((1<<(size*8))-1)
                self.put(address,value.to_bytes(size,'little'))
            else:value=int.from_bytes(uc.mem_read(address,size),'little')
            self.events.append(('read',address,size,value))
            if self.control_change and address==BASE+0x123c:
                self.values[BASE+0x1238]=self.control_change
        else:
            self.events.append(('write',address,size,value))
            if BASE<=address<BASE+0x2000:self.values[address]=value
    def execute(self,entry,args,count=2000000):
        try:
            preserved=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
            for i,reg in enumerate(preserved):self.cpu.reg_write(reg,0xa5c30000+i*0x123)
            value=self.call(self.compiled[1][ENTRIES[entry]] if self.compiled else entry,*args,count=count)
            assert [self.cpu.reg_read(reg) for reg in preserved]==[0xa5c30000+i*0x123 for i in range(8)]
            assert self.cpu.reg_read(UC_ARM_REG_SP)==0x20000ff0
            return ('return',value if entry<0x8000 else None)
        except AccessFault as error:return ('access-fault',error.args)
        except UcError as error:return ('cpu-fault',error.errno)
        except RuntimeError:return ('budget',)

class Pair:
    def __init__(self,compiled):self.a=HalOracle();self.b=HalOracle(compiled)
    def put(self,address,data):
        for o in (self.a,self.b):o.put(address,data)
    def regs(self,values,scripts=None):
        for o in (self.a,self.b):
            o.values={BASE+k:v for k,v in values.items()}
            o.scripts={BASE+k:deque(v) for k,v in (scripts or {}).items()}
    def run(self,entry,*args,count=2000000):
        a=self.a.execute(entry,args,count);b=self.b.execute(entry,args,count)
        assert a==b,(hex(entry),a,b)
        assert self.a.events==self.b.events,(hex(entry),self.a.events[:20],self.b.events[:20])
        assert self.a.values==self.b.values
        assert not self.a.hook_calls and not self.b.hook_calls
        return a

@pytest.mark.parametrize('entry,base,length',[(0x7a68,0x200000f4,6),(0x7a90,0x20000148,3)])
def test_table_lookup_full_byte_domain_duplicate_precedence_and_full_width_id(compiled,entry,base,length):
    p=Pair(compiled)
    for ids in [list(range(length)),[255]*length,[17,0,17,254,255,17][:length]]:
        blob=bytearray(length*12)
        for i,value in enumerate(ids):blob[i*12]=value
        p.put(base,blob)
        for key in [*range(256),256,257,0x10000,0x7fffffff,0x80000000,0xffffffff]:
            p.a.events.clear();p.b.events.clear()
            result=p.run(entry,key)
            expected=base+12*ids.index(key) if key in ids else 0
            assert result==('return',expected)

@pytest.mark.parametrize('entry',[0x7ac0,0x7ad4])
def test_direct_index_lookup_unsigned_boundary_and_does_not_dereference(compiled,entry):
    p=Pair(compiled)
    for key in [*range(257),65535,65536,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]:
        p.run(entry,key)
        assert not p.a.events

@pytest.mark.parametrize('entry',[0x930c,0x934c,0x9664,0x9688])
def test_configuration_bit_domains_access_order_and_reserved_bit_preservation(compiled,entry):
    rng=random.Random(entry);p=Pair(compiled)
    # Exhaust all byte values; cover every single input bit plus random combined
    # word fields and independently varied old register bits.
    configs=[bytes([v,255-v])+struct.pack('<HII',v*257,1<<(v%32),~(1<<((v+11)%32))&0xffffffff) for v in range(256)]
    configs += [rng.randbytes(12) for _ in range(80)]
    for config in configs:
        p.put(CFG,config)
        p.regs({o:rng.getrandbits(32) for o in [0x808,0x1100,0x1110,0x1004,0x1000,0x1108,0x1008]})
        p.a.events.clear();p.b.events.clear()
        assert p.run(entry,BASE,CFG)==('return',None)

@pytest.mark.parametrize('entry',[0x930c,0x934c,0x9664,0x9688])
def test_configuration_fault_at_each_access_preserves_prefix_and_bad_pointer(compiled,entry):
    config=bytes(range(12));regs={o:0xa5a55a5a for o in [0x808,0x1100,0x1110,0x1004,0x1000,0x1108,0x1008]}
    p=Pair(compiled);p.put(CFG,config);p.regs(regs);p.run(entry,BASE,CFG)
    for position in range(len(p.a.events)):
        q=Pair(compiled);q.put(CFG,config);q.regs(regs)
        q.a.fail_at=q.b.fail_at=position
        assert q.run(entry,BASE,CFG)[0]=='access-fault'
    q=Pair(compiled);q.regs(regs)
    assert q.run(entry,BASE,0x30000000)[0]=='cpu-fault'
    q=Pair(compiled);q.put(CFG,config)
    assert q.run(entry,0x30000000,CFG)[0]=='cpu-fault'

@pytest.mark.parametrize('entry,ready,busy,controlbit',[(0x93a0,0x800,0x700,0x80),(0x93d0,0,7,0x8000),(0x964c,0,0x80,0)])
def test_volatile_polling_ready_late_reserved_bits_and_control_reread(compiled,entry,ready,busy,controlbit):
    for delay in range(17):
        p=Pair(compiled);status=0x1108 if entry==0x964c else 0x123c
        p.regs({0x1238:0x12345678,status:busy}, {status:[busy]*delay+[ready]})
        if controlbit:p.a.control_change=p.b.control_change=0xdeadbeef
        assert p.run(entry,BASE,*([0xfedcba98] if entry==0x964c else []))==('return',None)
        if controlbit:assert p.a.values[BASE+0x1238]==0xdeadbeef&~controlbit
        else:assert p.a.values[BASE+0x1120]==0xfedcba98

@pytest.mark.parametrize('entry,status,busy',[(0x93a0,0x123c,0x700),(0x93d0,0x123c,1),(0x964c,0x1108,0x80)])
def test_polling_stuck_negative_control_never_fabricates_completion(compiled,entry,status,busy):
    p=Pair(compiled);p.regs({0x1238:0x405,status:busy})
    p.a.stop_after=p.b.stop_after=200
    assert p.run(entry,BASE,*([0x55] if entry==0x964c else []))[0]=='access-fault'
    writes=[e for e in p.a.events if e[0]=='write']
    assert len(writes)==(0 if entry==0x964c else 1)
    # The hook only stops a test; it does not release the polling condition.
    assert p.a.events[-1]==('read',BASE+status,4,busy)

def test_tx_fill_count_zero_full_fifo_partial_and_full_byte_values(compiled):
    for length in [0,1,2,7,8,255,256]:
        for available in [0,1,3,8,256]:
            p=Pair(compiled);p.put(DATA,bytes(range(256)))
            p.regs({0x123c:0}, {0x123c:[0x100]*available+[0]})
            assert p.run(0x9374,BASE,DATA,length)==('return',None)
            writes=[e[3] for e in p.a.events if e[0]=='write']
            assert writes==list(range(min(length,available)))

def test_tx_fill_uint16_compare_wrap_keeps_uint32_data_index(compiled):
    # 65536 is above every possible truncated comparison value. The terminating
    # condition must be FIFO availability, never a silently widened comparison.
    for count in [65535,65536,65537,0xffffffff]:
        p=Pair(compiled);p.put(DATA,bytes(range(256))*257)
        p.regs({0x123c:0}, {0x123c:[0x100]*65538+[0]})
        assert p.run(0x9374,BASE,DATA,count)==('return',None)
        writes=[e for e in p.a.events if e[0]=='write']
        assert len(writes)==(65535 if count==65535 else 65538)
        reads=[e[1] for e in p.a.events if e[0]=='read' and DATA<=e[1]<DATA+0x20000]
        assert reads==list(range(DATA,DATA+len(writes)))

def test_tx_fill_fault_is_ordered_after_status_read_and_before_data_write(compiled):
    p=Pair(compiled);p.regs({0x123c:0x100})
    assert p.run(0x9374,BASE,0x30000000,1)[0]=='cpu-fault'
    assert p.a.events==[('read',BASE+0x123c,4,0x100)]
    p=Pair(compiled);p.regs({0x123c:0})
    assert p.run(0x9374,BASE,0x30000000,1)==('return',None)


@pytest.mark.parametrize('entry,length',[(0x7a68,6),(0x7a90,3)])
def test_lookup_faults_preserve_each_table_read_boundary(compiled,entry,length):
    for position in range(length):
        p=Pair(compiled);p.a.fail_at=p.b.fail_at=position
        assert p.run(entry,0xffffffff)[0]=='access-fault'
        assert len(p.a.events)==position

@pytest.mark.parametrize('entry,mask,ready,status',[(0x93a0,0xf00,0x800,0x123c),(0x93d0,15,0,0x123c),(0x964c,0x80,0,0x1108)])
def test_polling_full_relevant_status_bit_domain_and_unrelated_bits(compiled,entry,mask,ready,status):
    for bits in range(16 if entry!=0x964c else 256):
        value=bits<<8 if entry==0x93a0 else bits
        value|=0xa55a0000
        p=Pair(compiled);p.regs({0x1238:0xffffffff,status:value},{status:[value,0xdead0000|ready]})
        p.run(entry,BASE,*([0xffffffff] if entry==0x964c else []))
        reads=[e for e in p.a.events if e[0]=='read' and e[1]==BASE+status]
        assert len(reads)==(1 if value&mask==ready else 2)

@pytest.mark.parametrize('entry',[0x930c,0x934c,0x9664,0x9688])
def test_config_single_bit_basis_includes_every_input_and_prior_register_bit(compiled,entry):
    p=Pair(compiled);offsets=[0x808,0x1100,0x1110,0x1004,0x1000,0x1108,0x1008]
    for inverted in [False,True]:
        for bit in range(96):
            raw=(1<<bit)^(((1<<96)-1) if inverted else 0)
            p.put(CFG,raw.to_bytes(12,'little'))
            p.regs({offset:((1<<(bit%32))^(0xffffffff if inverted else 0)) for offset in offsets})
            p.a.events.clear();p.b.events.clear();p.run(entry,BASE,CFG)


@pytest.mark.parametrize('entry,config_offset',[(0x930c,0x807),(0x934c,0x1003),(0x9664,0x10fc),(0x9688,0x1007)])
def test_configuration_aliasing_mmio_preserves_volatile_access_sequence(compiled,entry,config_offset):
    p=Pair(compiled)
    offsets=set([0x808,0x1100,0x1110,0x1004,0x1000,0x1108,0x1008])
    offsets.update(config_offset+i for i in [0,1,2,4,8])
    p.regs({offset:((offset*0x1234567)^0xa5c30000)&0xffffffff for offset in offsets})
    assert p.run(entry,BASE,BASE+config_offset)==('return',None)
