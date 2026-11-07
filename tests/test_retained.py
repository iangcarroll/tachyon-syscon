import ctypes as C
import random
import struct
from timer_oracle import TimerOracle
from test_timers import READ,WRITE


def test_retained_state_invalid_magic_masks_saturation_and_register_trace(lib):
    lib.syscon_retained_load.argtypes=[C.c_void_p,READ,WRITE,C.c_void_p]
    lib.syscon_retained_commit.argtypes=[C.c_void_p,WRITE,C.c_void_p]
    lib.syscon_retained_clear_registers.argtypes=[WRITE,C.c_void_p]
    for name in ('modem','battery'):
        getattr(lib,'syscon_retained_set_'+name).argtypes=[C.c_void_p,C.c_uint8,WRITE,C.c_void_p]
    lib.syscon_retained_increment_boots.argtypes=[C.c_void_p,WRITE,C.c_void_p]
    rng=random.Random(0x59d8)
    for valid in (False,True):
        o=TimerOracle()
        state=C.create_string_buffer(3)
        registers={0x400b0400:(rng.getrandbits(24)<<8)|(0x5b if valid else 0xc7),
                   0x400b0404:rng.getrandbits(32),0x400b0408:rng.getrandbits(32)}
        for a,v in registers.items():o.put(a,struct.pack('<I',v))
        trace=[]
        def read(_,a): trace.append(('read',a,4,registers[a])); return registers[a]
        def write(_,a,v): trace.append(('write',a,4,v)); registers[a]=v
        rd,wr=READ(read),WRITE(write)
        o.call(0x59d8);lib.syscon_retained_load(state,rd,wr,None)
        def compare():
            assert state.raw==bytes(o.cpu.mem_read(o.RETAINED,3))
            assert trace==o.mmio
            for name,address in [('modem',0x5ac4),('battery',0x5af0),('boots',0x5b14)]:
                assert getattr(lib,'syscon_retained_'+name)(state)==o.call(address)
        compare()
        for value in range(256):
            o.call(0x5aa8,value);lib.syscon_retained_set_modem(state,value,wr,None);compare()
            o.call(0x5ad4,255-value);lib.syscon_retained_set_battery(state,255-value,wr,None);compare()
            o.call(0x5afc);lib.syscon_retained_increment_boots(state,wr,None);compare()
        for _ in range(4):
            o.call(0x59d8);lib.syscon_retained_load(state,rd,wr,None);compare()
        before=state.raw
        o.call(0x5a88);lib.syscon_retained_clear_registers(wr,None);compare()
        assert state.raw==before
        o.call(0x59d8);lib.syscon_retained_load(state,rd,wr,None);compare()


def test_retained_commit_uses_snapshot_before_register_writes(lib):
    from unicorn import UC_HOOK_MEM_WRITE
    lib.syscon_retained_commit.argtypes=[C.c_void_p,WRITE,C.c_void_p]
    o=TimerOracle()
    initial=b'\x5b\xab\x7f'
    changed=b'\x01\x23\x45'
    o.put(o.RETAINED,initial)
    state=C.create_string_buffer(initial,3)
    trace=[]
    def original(uc,access,address,size,value,_):
        if address==0x400b0400: o.put(o.RETAINED,changed)
    o.cpu.hook_add(UC_HOOK_MEM_WRITE,original,begin=0x400b0400,end=0x400b040b)
    def native(_,address,value):
        trace.append(('write',address,4,value))
        if address==0x400b0400: C.memmove(state,changed,3)
    wr=WRITE(native)
    o.call(0x59a0);lib.syscon_retained_commit(state,wr,None)
    assert state.raw==bytes(o.cpu.mem_read(o.RETAINED,3))
    assert trace==o.mmio
