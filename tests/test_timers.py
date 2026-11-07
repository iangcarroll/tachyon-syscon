import ctypes as C
import random
import struct
import pytest
from timer_oracle import TimerOracle
from unicorn.arm_const import UC_ARM_REG_R1

CALL=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32,C.c_uint32)
READ=C.CFUNCTYPE(C.c_uint32,C.c_void_p,C.c_uint32)
WRITE=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32,C.c_uint32)
FEED=C.CFUNCTYPE(None,C.c_void_p)


@pytest.fixture
def timer_lib(lib):
    lib.syscon_timer_register.argtypes=[C.c_void_p,C.c_uint32,C.c_uint8,C.c_uint32,C.c_uint32]
    lib.syscon_timer_unregister.argtypes=[C.c_void_p,C.c_uint32]
    lib.syscon_timer_tick.argtypes=[C.c_void_p,CALL,C.c_void_p]
    lib.syscon_timer_init.argtypes=[C.c_void_p,READ,WRITE,C.c_void_p]
    lib.syscon_timer_now.argtypes=[C.c_void_p]
    lib.syscon_timer_now.restype=C.c_uint64
    return lib


def test_timer_random_sequences_preserve_slots_and_callback_trace(timer_lib):
    lib=timer_lib
    rng=random.Random(0x781c)
    callbacks=[0,0x10021,0x10025,0x10029,0x1002d,0x10031]
    for start in (0,0xffffffff,0xfffffffffffffff0):
        o=TimerOracle()
        initial=bytearray(rng.randbytes(112))
        for i in range(4): struct.pack_into('<I',initial,24*i+16,0)
        struct.pack_into('<Q',initial,104,start)
        state=C.create_string_buffer(bytes(initial),112)
        o.put(o.STATE,initial)
        calls=[]
        callback=CALL(lambda _,fn,arg:calls.append((fn,arg)))
        for step in range(800):
            kind=rng.randrange(5)
            fn=rng.choice(callbacks)
            if kind<2:
                args=(rng.choice([0,1,2,50,0xffffffff]),rng.choice([0,1,255]),fn,rng.getrandbits(32))
                expected=C.c_int32(o.call(0x781c,*args)).value
                assert lib.syscon_timer_register(state,*args)==expected
            elif kind==2:
                o.call(0x7880,fn)
                lib.syscon_timer_unregister(state,fn)
            else:
                o.call(0x76f8)
                lib.syscon_timer_tick(state,callback,None)
            assert state.raw==o.state(),(start,step)
            assert calls==o.callbacks
            assert lib.syscon_timer_now(state)==o.now()
            lo=o.call(0x77b4)
            assert lib.syscon_timer_now(state)==lo|(o.cpu.reg_read(UC_ARM_REG_R1)<<32)


def test_timer_callback_can_mutate_itself_later_slots_and_clock(timer_lib):
    lib=timer_lib
    for mutation in ('cancel','replace','arm-later','change-clock'):
        o=TimerOracle()
        state=C.create_string_buffer(112)
        o.put(o.STATE,b'\0'*112)
        for args in ((0,0,0x10021,11),(0,1,0x10025,22)):
            o.call(0x781c,*args)
            lib.syscon_timer_register(state,*args)
        calls=[]
        def changes(fn):
            if fn!=0x10021: return []
            if mutation=='cancel': return [(16,b'\0'*8)]
            if mutation=='replace': return [(12,b'\x01'),(16,struct.pack('<II',0x10029,99))]
            if mutation=='arm-later': return [(48,struct.pack('<QIB3xII',0,0,1,0x10029,33))]
            return [(104,struct.pack('<Q',0xffffffffffffffff))]
        def native(_,fn,arg):
            calls.append((fn,arg))
            for offset,data in changes(fn): C.memmove(C.addressof(state)+offset,data,len(data))
        def original(cpu,fn,arg):
            for offset,data in changes(fn): cpu.put(cpu.STATE+offset,data)
        o.callback_action=original
        callback=CALL(native)
        for _ in range(3):
            o.call(0x76f8)
            lib.syscon_timer_tick(state,callback,None)
            assert state.raw==o.state(),mutation
            assert calls==o.callbacks,mutation


def test_timer_init_mmio_and_idempotence(timer_lib):
    lib=timer_lib
    rng=random.Random(0x776c)
    for initialized in (0,1,255):
        o=TimerOracle()
        data=bytearray(rng.randbytes(112)); data[96]=initialized
        o.put(o.STATE,data)
        state=C.create_string_buffer(bytes(data),112)
        registers={0xe000ed20:rng.getrandbits(32)}
        for a,v in registers.items():o.put(a,struct.pack('<I',v))
        trace=[]
        def read(_,address):
            trace.append(('read',address,4,registers[address])); return registers[address]
        def write(_,address,value):
            trace.append(('write',address,4,value));registers[address]=value
        rd,wr=READ(read),WRITE(write)
        for _ in range(2):
            o.call(0x776c)
            lib.syscon_timer_init(state,rd,wr,None)
            assert state.raw==o.state()
            assert trace==o.mmio


def test_timer_delays_with_explicit_external_clock_and_countflag_progress(timer_lib):
    lib=timer_lib
    lib.syscon_timer_delay.argtypes=[C.c_void_p,C.c_uint32,FEED,C.c_void_p]
    lib.syscon_timer_wait_countflags.argtypes=[C.c_uint32,READ,C.c_void_p]
    for start in (0,0xffffffff,0xfffffffffffffff0):
        for duration in (0,1,7,300):
            o=TimerOracle()
            initial=bytearray(112);struct.pack_into('<Q',initial,104,start)
            state=C.create_string_buffer(bytes(initial),112);o.put(o.STATE,initial)
            calls=[0,0]
            def original(cpu):
                calls[0]+=1
                cpu.put(cpu.STATE+104,struct.pack('<Q',(cpu.now()+3)&0xffffffffffffffff))
            def native(_):
                calls[1]+=1
                value=(lib.syscon_timer_now(state)+3)&0xffffffffffffffff
                C.memmove(C.addressof(state)+104,struct.pack('<Q',value),8)
            o.hooks[0x79d0]=original
            feed=FEED(native)
            o.call(0x77c0,duration);lib.syscon_timer_delay(state,duration,feed,None)
            assert calls[0]==calls[1]
            assert state.raw==o.state()
    for count in (0,1,2,100):
        o=TimerOracle();reads=[0,0]
        # Hook runs before the original MMIO read and supplies a scripted
        # COUNTFLAG sequence; these are external events, not simulated timers.
        from unicorn import UC_HOOK_MEM_READ
        def flag_read(uc,access,address,size,value,_):
            reads[0]+=1
            uc.mem_write(address,struct.pack('<I',0x10007 if reads[0]%3 else 7))
        o.cpu.hook_add(UC_HOOK_MEM_READ,flag_read,begin=0xe000e010,end=0xe000e013)
        def native(_,address):
            assert address==0xe000e010
            reads[1]+=1
            return 0x10007 if reads[1]%3 else 7
        rd=READ(native)
        o.call(0x77fc,count);lib.syscon_timer_wait_countflags(count,rd,None)
        assert reads[0]==reads[1]
