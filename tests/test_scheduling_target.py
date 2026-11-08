"""Actual ARM target ABI, direct compiled callbacks and ordered MMIO effects.

The original side redirects logger/watchdog *entry* to the compiled fixture;
it does not replace timer/task callbacks, memory helpers, or the tested bodies.
The rebuilt side never executes an original instruction.
"""
import random
import struct
from pathlib import Path
import pytest
from elftools.elf.elffile import ELFFile
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_WRITE,UC_PROT_READ,UC_PROT_EXEC,UcError
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_R1,UC_ARM_REG_PRIMASK,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11
from arm_rebuild_oracle import ArmRebuildOracle
from oracle import Oracle,REPLACED_ENDPOINTS,EXECUTED_ORIGINAL
from power_state_comparison import text_argument
from build_scheduling_target import build,MAPPINGS

E=0x21008000
T=0x20000610
Q=0x20000534
R=0x200000da
CALLEE=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]

@pytest.fixture(scope='module')
def scheduling_elf(tmp_path_factory):return build(tmp_path_factory.mktemp('scheduling-target')/'test.elf')

class Original(Oracle):
    def __init__(self,elf,reference):
        self.redirect={0x8f88:reference.symbols['syscon_target_logger'],
                       0x79d0:reference.symbols['syscon_target_watchdog_feed']}
        super().__init__()
        self.cpu.mem_map(reference.CODE,0x100000)
        self.cpu.mem_map(reference.DATA,0x10000)
        with Path(elf).open('rb') as f:
            for segment in ELFFile(f).iter_segments():
                if segment['p_type']=='PT_LOAD' and segment['p_filesz']:
                    self.put(segment['p_vaddr'],segment.data())
        self.cpu.mem_protect(reference.CODE,0x100000,UC_PROT_READ|UC_PROT_EXEC)
        self.cpu.mem_protect(0,0x10000,UC_PROT_READ|UC_PROT_EXEC)
    def _step(self,uc,address,size,_):
        if address in self.redirect:
            REPLACED_ENDPOINTS.add(address);uc.reg_write(UC_ARM_REG_PC,self.redirect[address]);return
        # Do not misclassify compiled fixture code as original firmware coverage.
        if address>=0x01000000:return
        super()._step(uc,address,size,_)
    def read(self,address,length):return bytes(self.cpu.mem_read(address,length))

class Pair:
    def __init__(self,elf):
        self.a=ArmRebuildOracle(elf);self.o=Original(elf,self.a)
        self.machines=(self.o,self.a);self.traces=[[],[]];self.ram_writes=[[],[]]
        for i,m in enumerate(self.machines):
            m.put(E,b'\0'*8192)
            m.put(E+8,struct.pack('<I',0x76f9 if i==0 else self.a.symbols['syscon_target_timer_tick']))
            for base in (0xe000e000,0x400b0000):m.cpu.mem_map(base,0x1000)
            def trace(uc,kind,address,size,value,_,index=i):
                if kind==UC_MEM_WRITE and 0x20000000<=address<0x20000d00:
                    self.ram_writes[index].append((address,size,value&((1<<(8*size))-1)))
                if (0xe000e000<=address<0xe000f000 or 0x400b0000<=address<0x400b1000):
                    observed=value&((1<<(8*size))-1) if kind==UC_MEM_WRITE else int.from_bytes(uc.mem_read(address,size),'little')
                    self.traces[index].append((kind,address,size,observed))
            m.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,trace)
    def put(self,address,data):
        for m in self.machines:m.put(address,data)
    def word(self,address,value):self.put(address,struct.pack('<I',value))
    def symbol(self,name):return self.a.symbols[name]
    def events(self,m):
        events=[]
        for offset in range(m.u32(E)):
            row=list(struct.unpack('<6I',m.read(E+64+24*offset,24)))
            if row[0]<=3:row[1],row[2]=text_argument(m,row[1]),text_argument(m,row[2])
            events.append(tuple(row))
        return events
    def run(self,entry,*args,returns=False):
        for m in self.machines:m.put(E,bytes(4))
        for trace in self.traces:trace.clear()
        for trace in self.ram_writes:trace.clear()
        before=[]
        for m in self.machines:
            m.cpu.reg_write(UC_ARM_REG_PRIMASK,1)
            for i,r in enumerate(CALLEE):m.cpu.reg_write(r,0x12345678+i)
            before.append([m.cpu.reg_read(r) for r in CALLEE])
        results=[self.o.call(entry,*args),self.a.call(MAPPINGS[entry],*args)]
        if returns:assert results[0]==results[1]
        # Whole persistent RAM plus guard bands; original/candidate stack scratch
        # is deliberately excluded (different legitimate stack frame layouts).
        assert self.o.read(0x20000000,0xd00)==self.a.read(0x20000000,0xd00)
        assert self.events(self.o)==self.events(self.a)
        assert self.traces[0]==self.traces[1]
        assert self.ram_writes[0]==self.ram_writes[1]
        for i,m in enumerate(self.machines):
            assert [m.cpu.reg_read(r) for r in CALLEE]==before[i]
            assert m.cpu.reg_read(UC_ARM_REG_PRIMASK)==1
        return results[0]

def test_timer_register_full_duplicate_zero_and_compiled_callback_sequences(scheduling_elf):
    rng=random.Random(0x781c)
    for start in (0,0xffffffff,0xfffffffffffffff0):
        p=Pair(scheduling_elf);p.put(T,bytes(112));p.put(T+104,struct.pack('<Q',start))
        callbacks=[0,p.symbol('fixture_timer_callback'),p.symbol('fixture_timer_alternate')]
        # Fill four slots with distinct valid Thumb addresses (the last two only
        # used to test registration failure/duplicate, then removed before tick).
        for callback in callbacks[1:]+[0x10001,0x10005]:
            assert p.run(0x781c,0,0,callback,callback,returns=True)==0
        assert p.run(0x781c,0,0,0x10009,0,returns=True)==0xffffffff
        p.run(0x781c,42,0xffffffff,callbacks[1],7,returns=True)
        for callback in (0x10001,0x10005):p.run(0x7880,callback)
        for _ in range(250):
            operation=rng.randrange(4);callback=rng.choice(callbacks)
            if operation<2:p.run(0x781c,rng.choice([0,1,2,0xffffffff]),rng.getrandbits(32),callback,rng.getrandbits(32),returns=True)
            elif operation==2:p.run(0x7880,callback)
            else:p.run(0x76f8)
            p.run(0x77b4,returns=True)
            assert p.o.cpu.reg_read(UC_ARM_REG_R1)==p.a.cpu.reg_read(UC_ARM_REG_R1)

@pytest.mark.parametrize('mode',[0,1,2,3,4])
def test_timer_real_callbacks_mutate_current_later_slots_and_clock(scheduling_elf,mode):
    p=Pair(scheduling_elf);p.put(T,bytes(112));p.word(E+4,mode);p.word(E+16,p.symbol('fixture_timer_alternate'))
    p.run(0x781c,0,0,p.symbol('fixture_timer_callback'),11,returns=True)
    p.run(0x781c,0,1,p.symbol('fixture_timer_alternate'),22,returns=True)
    for _ in range(3):p.run(0x76f8)
    assert any(p.symbol('fixture_timer_callback')&~1 in m.executed for m in (p.a,))

def test_timer_init_mmio_order_and_idempotence_preserves_clock(scheduling_elf):
    rng=random.Random(0x776c)
    for flag in (0,1,255):
        p=Pair(scheduling_elf);initial=bytearray(rng.randbytes(112));initial[96]=flag
        p.put(T,initial);p.word(0xe000ed20,rng.getrandbits(32));p.run(0x776c)
        assert p.a.read(T+104,8)==initial[104:112]
        p.run(0x776c);assert p.traces==[[],[]]

def test_clock_torn_read_is_not_replaced_with_atomic_retry(scheduling_elf):
    p=Pair(scheduling_elf);p.put(T+104,struct.pack('<Q',0xffffffff))
    for m in p.machines:
        def interrupt_between_words(uc,kind,address,size,value,_):
            if address==T+108:uc.mem_write(T+104,struct.pack('<Q',0x100000000))
        m.cpu.hook_add(UC_HOOK_MEM_READ,interrupt_between_words)
    assert p.run(0x77b4,returns=True)==0xffffffff
    assert [m.cpu.reg_read(UC_ARM_REG_R1) for m in p.machines]==[1,1]

@pytest.mark.parametrize('delay',[0,1,7])
def test_delay_executes_real_watchdog_dependency_and_tick(scheduling_elf,delay):
    p=Pair(scheduling_elf);p.put(T,bytes(112));p.put(T+104,struct.pack('<Q',0xffffffff))
    p.run(0x77c0,delay)
    assert [m.u32(E+12) for m in p.machines]==[delay,delay]
    assert p.a.symbols['syscon_target_watchdog_feed']&~1 in p.a.executed if delay else True

def test_countflag_consumption_including_initial_clear(scheduling_elf):
    for count in (0,1,5):
        p=Pair(scheduling_elf);access=[0,0]
        for i,m in enumerate(p.machines):
            def flags(uc,kind,address,size,value,_,index=i):
                if address==0xe000e010:
                    uc.mem_write(address,struct.pack('<I',0x10000 if access[index]%3==0 else 0));access[index]+=1
            m.cpu.hook_add(UC_HOOK_MEM_READ,flags)
        p.run(0x77fc,count);assert access[0]==access[1]==1+count*3

def test_scheduler_capacity_aliasing_callbacks_wait_and_failure_paths(scheduling_elf):
    p=Pair(scheduling_elf);p.put(T,bytes(112));p.word(E+20,1)
    p.put(Q,b'\xab'*216);p.run(0x7540)
    actions=b''.join(struct.pack('<B3xI',k,v) for k,v in [(0,p.symbol('fixture_task_callback')),(1,2),(7,0)])
    p.put(0x20000900,actions)
    assert p.run(0x7554,0x30000000,13,returns=True)==0xffffffff
    assert p.run(0x7554,0x20000900,3,returns=True)==0
    assert p.run(0x7554,0x20000900,0,returns=True)==1
    assert p.run(0x7554,0x30000000,0,returns=True)==0xffffffff
    for _ in range(8):
        p.run(0x75d8);p.run(0x76d8,returns=True);p.run(0x76f8)
    # Exact forward-copy behavior also applies to overlapping source/destination.
    p.run(0x7540);p.put(Q,actions+b'\x78'*80);p.put(Q+104,b'\0')
    p.run(0x7554,Q+1,12,returns=True)

@pytest.mark.parametrize('mode',[0,1,2,3,4])
@pytest.mark.parametrize('result',[0,1,0xffffffff])
def test_scheduler_real_callback_mutation_and_raw_nonboolean_result(scheduling_elf,mode,result):
    p=Pair(scheduling_elf);p.put(Q,bytes(216));p.put(T,bytes(112));p.word(E+4,mode);p.word(E+20,result)
    p.put(0x20000900,struct.pack('<B3xI',0,p.symbol('fixture_task_callback'))*12)
    p.run(0x7554,0x20000900,12,returns=True)
    for _ in range(2):p.run(0x75d8)

def test_scheduler_timestamp_zero_wrap_and_raw_active(scheduling_elf):
    for now in (0,1,0xffffffff,0x100000000,0xffffffffffffffff):
        p=Pair(scheduling_elf);p.put(Q,bytes(216));p.put(T+104,struct.pack('<Q',now))
        p.put(0x20000900,struct.pack('<B3xI',1,0xffffffff));p.run(0x7554,0x20000900,1,returns=True)
        for _ in range(3):p.run(0x75d8);p.run(0x76f8)
        for first,second in ((255,2),(0,17),(0,0)):
            p.put(Q+104,bytes([first]));p.put(Q+212,bytes([second]));p.run(0x76d8,returns=True)

def test_retained_load_logging_recheck_snapshot_and_all_nibbles(scheduling_elf):
    p=Pair(scheduling_elf);rng=random.Random(0x59d8)
    for magic in (0,0x5b,0x12345b,0xffffffff):
        for mutation in (0,0x5b,0x42):
            p.word(E+24,mutation);p.put(0x400b0400,struct.pack('<III',magic,0xabcd1234,0x9876ff))
            p.run(0x59d8)
    p.word(E+24,0)
    for value in list(range(256))+[rng.getrandbits(32) for _ in range(40)]:
        p.put(R,rng.randbytes(3));p.run(0x5aa8,value);p.run(0x5ac4,returns=True)
        p.run(0x5ad4,value);p.run(0x5af0,returns=True)
    for boots in (0,1,254,255):
        p.put(R+2,bytes([boots]));p.run(0x5afc);p.run(0x5b14,returns=True)
    p.run(0x5a88)
    # MMIO observers may mutate RAM after the first write. All writes must
    # still come from the pre-write snapshot.
    p.put(R,b'\x5b\x93\x72')
    for m in p.machines:
        def alter(uc,kind,address,size,value,_):
            if address==0x400b0400:uc.mem_write(R,b'\xee\xdd\xcc')
        m.cpu.hook_add(UC_HOOK_MEM_WRITE,alter)
    p.run(0x59a0)

def test_invalid_callback_and_source_fault_without_added_validation(scheduling_elf):
    p=Pair(scheduling_elf);p.put(T,bytes(112));p.run(0x781c,0,0,0x30000001,123,returns=True)
    for m,entry in ((p.o,0x76f8),(p.a,MAPPINGS[0x76f8])):
        with pytest.raises(UcError):m.call(entry)
        assert m.read(T+104,8)==struct.pack('<Q',1)
        assert m.u32(T+16)==0x30000001
    p=Pair(scheduling_elf);p.put(Q,bytes(216))
    for m,entry in ((p.o,0x7554),(p.a,MAPPINGS[0x7554])):
        with pytest.raises(UcError):m.call(entry,0x30000000,1)
        assert m.read(Q,216)==bytes(216)

@pytest.fixture(scope='module')
def physical_scheduling_fixture(tmp_path_factory):
    elf=build(tmp_path_factory.mktemp('scheduling-physical')/'test.elf',physical_fixture=True)
    with elf.open('rb') as f:
        parsed=ELFFile(f)
        segments=[(s['p_vaddr'],s.data()) for s in parsed.iter_segments() if s['p_type']=='PT_LOAD']
        symbols={s.name:s['st_value'] for s in parsed.get_section_by_name('.symtab').iter_symbols()}
    return segments,symbols

@pytest.mark.parametrize('psp',[False,True])
def test_actual_systick_exception_executes_target_handler_and_callback_without_hooks(physical_scheduling_fixture,psp):
    from mspm0.core import MCU
    from inventory import load_image
    from unicorn.arm_const import UC_ARM_REG_MSP,UC_ARM_REG_PSP,UC_ARM_REG_CONTROL,UC_ARM_REG_R0,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12,UC_ARM_REG_LR
    segments,symbols=physical_scheduling_fixture
    states=[];machines=[]
    for original in (True,False):
        # Original bytes are present ONLY in the reference. Candidate code,
        # vectors, and callback pointers all come from our sources/test setup.
        image=bytearray(load_image() if original else b'\xff'*65536)
        for address,data in segments:image[address:address+len(data)]=data
        struct.pack_into('<II',image,0,0x20001000,symbols['fixture_thread'])
        struct.pack_into('<I',image,15*4,0x76f9 if original else symbols['syscon_target_timer_tick'])
        m=MCU(image,peripherals=False);machines.append(m)
        m.write_ram(T,struct.pack('<QIB3xII',0,0,1,symbols['fixture_timer_callback'],0x12345678))
        if psp:
            m.cpu.reg_write(UC_ARM_REG_PSP,0x20000e00);m.cpu.reg_write(UC_ARM_REG_CONTROL,2)
        assert m.run(50)[0]=='wfi'
        saved=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12,UC_ARM_REG_LR]+CALLEE
        m.cpu.reg_write(UC_ARM_REG_PRIMASK,1);m.pend(15)
        m.run(2)
        assert 15 in m.pending and not m.active and m.read(T+104,8)==bytes(8)
        # Wake may execute thread instructions with PRIMASK set, so snapshot
        # caller state at the actual preemption boundary.
        for i,r in enumerate(saved):m.cpu.reg_write(r,0x12345678+i)
        before=[m.cpu.reg_read(r) for r in saved]
        pc=m.cpu.reg_read(UC_ARM_REG_PC)
        m.cpu.reg_write(UC_ARM_REG_PRIMASK,0)
        m.run(1);assert m.active==[15]
        m.breakpoints.add(pc)
        m.run(1000)
        assert not m.active and m.cpu.reg_read(UC_ARM_REG_PC)==pc
        assert [m.cpu.reg_read(r) for r in saved]==before
        assert m.read(T+104,8)==struct.pack('<Q',1)
        assert int.from_bytes(m.read(0x20000920,4),'little')==15
        assert any(event[:2]==('exception-enter',15) for event in m.events)
        assert any(event[0]=='exception-return' for event in m.events)
        assert m.cpu.reg_read(UC_ARM_REG_CONTROL)==(2 if psp else 0)
        assert m.cpu.reg_read(UC_ARM_REG_MSP)==0x20001000
        if psp:assert m.cpu.reg_read(UC_ARM_REG_PSP)==0x20000e00
        states.append(m.read(0x20000000,0xd00))
    assert states[0]==states[1]
    # Negative control: an invalid vector is rejected by the physical model;
    # it is not silently substituted by the native timer model.
    from mspm0.core import BusFault
    bad=bytearray(image);struct.pack_into('<I',bad,15*4,symbols['syscon_target_timer_tick']&~1)
    m=MCU(bad,peripherals=False);m.pend(15)
    with pytest.raises(BusFault):m.run(100)


def test_scheduler_and_retained_logs_survive_poisoned_legacy_text(scheduling_elf):
    p=Pair(scheduling_elf)
    p.a.put(0xcdab,b'\xa5'*(0xcdf0-0xcdab))
    p.a.put(0xdbf6,b'\xa5'*(0xdd05-0xdbf6))
    p.word(0x400b0400,0x12)
    p.run(0x59d8)
    assert p.a.read(R,3)==bytes([0x5b,0,0])
    p.run(0x7540)
    p.run(0x7554,0,13,returns=True)
    actions=0x20000900
    p.put(actions,struct.pack('<B3xI',1,1))
    p.run(0x7554,actions,1,returns=True)
    assert p.a.call('syscon_target_tasks_active')==1
    p.put(T+104,struct.pack('<Q',1));p.run(0x75d8)
    p.put(T+104,struct.pack('<Q',2));p.run(0x75d8)
    assert p.a.call('syscon_target_tasks_active')==0
