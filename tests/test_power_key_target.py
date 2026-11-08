import random
import struct
import pytest
from unicorn import UcError
from unicorn.arm_const import UC_ARM_REG_PRIMASK
from build_power_key_target import build,MAPPINGS
from build_scheduling_target import MAPPINGS as TIMER_MAPPINGS
from test_scheduling_target import Pair,E,T,CALLEE

@pytest.fixture(scope='module')
def power_key_elf(tmp_path_factory):return build(tmp_path_factory.mktemp('powerkey-target')/'test.elf')

class KeyPair(Pair):
    def __init__(self,elf):
        super().__init__(elf)
        for entry,name in [(0x80f8,'gpio_read'),(0x81f8,'gpio_detach'),(0x8148,'gpio_attach'),
            (0x7f58,'gpio_config'),(0x6690,'modem_off'),(0x6a28,'modem_key_assert'),(0x6a48,'modem_key_release'),
            (0x315c,'edl_timer_seconds'),(0x3178,'shutdown_timer_seconds')]:
            self.o.redirect[entry]=self.symbol('syscon_target_'+name)
        self.entries=TIMER_MAPPINGS|MAPPINGS
        self.pointers={entry|1:self.symbol(MAPPINGS[entry]) for entry in (0x570c,0x5740,0x5844)}
        self.word(E+24,3);self.word(E+28,5)
    def norm_pointer(self,value):return self.pointers.get(value,value)
    def norm_state(self,state):
        state=bytearray(state)
        for offset in range(0x620,0x670,24):
            value=struct.unpack_from('<I',state,offset)[0]
            struct.pack_into('<I',state,offset,self.norm_pointer(value))
        return state
    def norm_events(self,machine):
        def string(address):
            value=bytearray()
            for i in range(256):
                byte=machine.read(address+i,1)
                if byte==b'\0':return bytes(value)
                value.extend(byte)
            raise AssertionError('Unterminated logger string')
        events=[]
        for record in self.events(machine):
            kind,a,b,c,d,e=record
            if kind==0x8148:
                c=self.norm_pointer(c)
            elif kind==0x8f88:
                # Logger pointers are compared by string content. Integer
                # arguments and callback/context pointers stay exact.
                b,c,d=string(b),string(c),string(d)
            events.append((kind,a,b,c,d,e))
        return events
    def norm_writes(self,writes):
        return [(a,n,self.norm_pointer(v) if a in range(T+16,T+96,24) else v) for a,n,v in writes]
    def run(self,entry,*args,returns=False):
        for m in self.machines:
            m.put(E,bytes(4));m.cpu.reg_write(UC_ARM_REG_PRIMASK,1)
            for i,r in enumerate(CALLEE):m.cpu.reg_write(r,0xa1234567+i)
        for trace in self.traces+self.ram_writes:trace.clear()
        original=self.o.call(entry,*args)
        # Only self-referential firmware function pointers are relocated. User
        # callback/context pointers are identical and are never translated.
        rebuilt=self.a.call(self.entries[entry],*args)
        if returns:assert original==rebuilt
        assert self.norm_state(self.o.read(0x20000000,0xd00))==self.a.read(0x20000000,0xd00)
        assert self.norm_events(self.o)==self.norm_events(self.a)
        assert self.norm_writes(self.ram_writes[0])==self.ram_writes[1]
        assert self.traces[0]==self.traces[1]
        assert all(m.cpu.reg_read(UC_ARM_REG_PRIMASK)==1 for m in self.machines)
        for m in self.machines:assert [m.cpu.reg_read(r) for r in CALLEE]==[0xa1234567+i for i in range(len(CALLEE))]
        return original

def test_powerkey_logging_does_not_read_original_private_strings(power_key_elf):
    p=KeyPair(power_key_elf)
    p.a.put(0xcd7b,b'\xa5'*(0xcdab-0xcd7b))
    p.put(T,bytes(112))
    # Both modes and a nonzero input that truncates to zero must retain the
    # original messages, while candidate strings live in its relocated ELF.
    for mode in (0,1,256):
        p.run(0x591c,mode)


def test_powerkey_init_mode_original_input_word_logging_and_callback_registration(power_key_elf):
    for mode in (0,1,255,256,0xffffffff):
        p=KeyPair(power_key_elf);p.put(T,bytes(112));p.word(0xe000ed20,0x12345678)
        p.run(0x5970,mode,returns=True)
        p.run(0x5908,p.symbol('fixture_key_callback'),0xaabbccdd,returns=True)
        p.run(0x591c,mode)
        p.run(0x5908,0,0xffffffff,returns=True)

@pytest.mark.parametrize('mode',[0,1,255])
@pytest.mark.parametrize('high',[0,1,0xffffffff])
def test_powerkey_edge_to_real_timer_debounce_and_repeating_poll(power_key_elf,mode,high):
    p=KeyPair(power_key_elf);p.put(T,bytes(112));p.run(0x5970,mode,returns=True)
    p.word(E+4,high);p.word(E+20,1)
    p.run(0x5908,p.symbol('fixture_key_callback'),0x20000700,returns=True)
    p.run(0x570c,0x12340000,returns=True)
    for _ in range(45):p.run(0x76f8)
    assert p.a.symbols['syscon_target_powerkey_debounce']&~1 in p.a.executed

def test_powerkey_debounce_modem_state_threshold_overflow_and_dependency_mutation(power_key_elf):
    for mode,high,event,off,seconds,mutation in [
        (mode,high,event,off,seconds,mutation)
        for mode in (0,1) for high in (0,1) for event in (0,255)
        for off in (0,2) for seconds in (0,3,0xffffffff) for mutation in (0,1)]:
        p=KeyPair(power_key_elf);p.put(T,bytes(112));p.put(0x200000d8,bytes([mode,event]))
        p.word(E+4,high);p.word(E+16,mutation);p.word(E+20,off);p.word(E+24,seconds);p.word(E+28,seconds)
        p.run(0x5844,0xaabbccdd)

@pytest.mark.parametrize('mutation',[0,1,2,3])
def test_powerkey_user_callback_mutates_event_pending_callback_and_context(power_key_elf,mutation):
    p=KeyPair(power_key_elf);p.put(T,bytes(112));p.word(E+32,mutation)
    p.run(0x5908,p.symbol('fixture_key_callback'),0xf1234567,returns=True)
    # Released long enough to fire event+1 and finish. Cleanup uses the local
    # completion decision even if the callback overwrites pending/event.
    p.put(0x200000d8,b'\x00\x03');p.put(0x2000039c,b'\x01');p.word(0x20000398,200)
    p.word(E+4,1);p.run(0x5740,0)
    assert p.a.u32(E+36)==p.o.u32(E+36)==1
    assert p.a.read(0x200000d9,1)==b'\xff' and p.a.read(0x2000039c,1)==b'\0'

def test_powerkey_poll_boundary_ranges_force_and_unsigned_wrap(power_key_elf):
    rng=random.Random(0x5740)
    cases=[(pressed,released,high,mode,forced,pending)
        for pressed in (0,9,2990,3000,5989,5990,6000,7990,8000,0xfffffff8)
        for released in (0,190,200,201,0xfffffff8)
        for high in (0,1) for mode in (0,1) for forced in (0,1) for pending in (0,1)]
    p=KeyPair(power_key_elf)
    for pressed,released,high,mode,forced,pending in cases:
        p.put(T,bytes(112));p.put(0x200000b4,struct.pack('<9I',10,3000,0,3000,8000,2,8000,0xffffffff,4))
        p.put(0x200000d8,bytes([mode,rng.choice([0,1,2,3,4,5,255])]))
        p.put(0x20000390,struct.pack('<III',pressed,p.symbol('fixture_key_callback'),released))
        p.put(0x2000039c,bytes([pending,forced,0,0]));p.word(0x200003a0,rng.getrandbits(32));p.word(E+4,high)
        p.run(0x5740,0)

def test_timer_full_failure_and_invalid_user_callback_are_not_hidden(power_key_elf):
    p=KeyPair(power_key_elf);p.put(T,bytes(112))
    # Four inert non-key pointers force debounce registration to fail; edge
    # still stores the truncated pin and detaches GPIO before returning -1.
    for i in range(4):p.put(T+24*i,struct.pack('<QIB3xII',0,0xffffffff,0,0x10001+4*i,0))
    assert p.run(0x570c,0x12345678,returns=True)==0xffffffff
    assert p.a.read(0x200003a4,2)==b'\x78\x56'
    p=KeyPair(power_key_elf);p.put(0x200000d8,b'\x00\x03');p.word(E+4,1)
    p.word(0x20000398,200);p.run(0x5908,0x30000001,0,returns=True)
    for m,entry in ((p.o,0x5740),(p.a,MAPPINGS[0x5740])):
        with pytest.raises(UcError):m.call(entry,0)
        assert m.read(0x200000d9,1)==b'\x04'
        assert m.read(0x2000039c,1)==b'\x01'

def test_complete_long_press_release_flow_runs_only_real_key_and_timer_instructions(power_key_elf):
    p=KeyPair(power_key_elf);p.put(T,bytes(112))
    p.put(0x200000b4,struct.pack('<9I',10,3000,0,3000,8000,2,8000,0xffffffff,4))
    p.word(E+20,1);p.run(0x5970,0,returns=True)
    p.run(0x5908,p.symbol('fixture_key_callback'),0xdeadbeef,returns=True)
    p.run(0x570c,0,returns=True)
    callbacks=[];forced=[]
    def tick():
        p.run(0x76f8)
        for record in p.events(p.a):
            if record[0]==0xf100:callbacks.append(record[1:3])
            if record[0]==0x6a48:forced.append(p.a.u32(0x20000390))
    for _ in range(6020):tick()
    assert p.a.read(0x2000039d,1)==b'\x01'
    p.word(E+4,1);p.run(0x570c,0,returns=True)
    for _ in range(240):tick()
    assert callbacks==[(0,0xdeadbeef),(2,0xdeadbeef),(3,0xdeadbeef)]
    assert forced[0]==6000
    assert p.a.read(0x200000d9,1)==b'\xff'
    assert all(p.a.u32(T+16+24*i)==0 for i in range(4))
