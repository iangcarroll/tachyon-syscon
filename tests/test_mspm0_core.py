import ctypes as C
import random
import struct
import pytest
from mspm0_core_oracle import MSPM0CoreOracle
from test_timers import READ,WRITE
from unicorn.arm_const import UC_ARM_REG_R1

DISPATCH=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32)
class Environment(C.Structure):
    _fields_=[('read',READ),('write',WRITE),('dispatch',DISPATCH),('ctx',C.c_void_p)]


def register_values(seed):
    rng=random.Random(seed)
    addresses=[0x40080804,0x40080800,0x40081104,0x40081100,0x40081108,
        0x400b0220,0x400b0104,0x40401130,0x400a1020,0xe000e100]
    addresses += [0x400a0000+x for x in (0x800,0x12e0,0x1290,0x12a0,0x12b0,0x12d0,0x1380,0x1390,0x13a0,0x1048,0x1028)]
    addresses += [0x40428004+pin*4 for pin in range(32)]
    return {a:rng.getrandbits(32) for a in addresses}


class Comparison:
    def __init__(self,lib,registers,initial=None):
        self.lib=lib
        self.o=MSPM0CoreOracle(registers)
        if initial is not None:self.o.put(0x20000000,initial)
        self.state=C.create_string_buffer(bytes(self.o.cpu.mem_read(0x20000000,4096)),4096)
        self.registers=dict(registers);self.trace=[];self.dispatch=[];self.errors=[]
        def read(_,a):
            if a not in self.registers:self.errors.append(('read',a));return 0
            value=self.registers[a];self.trace.append(('read',a,value));return value
        def write(_,a,v):
            if a not in self.registers:self.errors.append(('write',a))
            self.registers[a]=v;self.trace.append(('write',a,v))
        def dispatch(_,fn,a,b):self.dispatch.append((fn,a,b))
        self.rd=READ(read);self.wr=WRITE(write);self.cb=DISPATCH(dispatch)
        self.env=Environment(self.rd,self.wr,self.cb,None)
        lib.mspm0_core_execute.argtypes=[C.c_void_p,C.POINTER(Environment),C.c_uint32,C.c_uint32,
            C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p]
        lib.mspm0_core_execute.restype=C.c_uint64
        lib.mspm0_reset_init.argtypes=[C.c_void_p,C.c_void_p,C.POINTER(Environment)]

    def compare(self):
        assert not self.errors,self.errors
        assert self.state.raw[:0xf00]==bytes(self.o.cpu.mem_read(0x20000000,0xf00))
        assert self.trace==self.o.trace
        assert self.registers==self.o.registers
        assert self.dispatch==self.o.dispatch

    def run(self,entry,pin=0,a=0,b=0,c=0,cfg=None,returns=True):
        if cfg is not None:
            self.o.put(0x20000f00,cfg)
            expected=self.o.call(entry,pin,0x20000f00)
        else:expected=self.o.call(entry,pin,a,b,c)
        got=self.lib.mspm0_core_execute(self.state,C.byref(self.env),entry,pin,a,b,c,C.c_char_p(cfg) if cfg else None)
        if returns:assert got&0xffffffff==expected,(hex(entry),got,expected)
        if entry==0x8148:assert got>>32==self.o.cpu.reg_read(UC_ARM_REG_R1)
        self.compare()
        return got


def test_watchdog_init_feed_exact_register_trace(lib):
    for seed in range(4):
        cmp=Comparison(lib,register_values(seed))
        for entry in (0x798c,0x79d0,0x79d0,0x798c,0x7be0,0x7be0):cmp.run(entry)
        cmp.run(0x7a50,returns=False)


def test_reset_copies_both_initialized_regions_and_only_clears_bss(lib):
    rng=random.Random(0x79f0)
    for _ in range(4):
        cmp=Comparison(lib,{},rng.randbytes(4096))
        cmp.o.call(0x79f0)
        lib.mspm0_reset_init(cmp.state,C.c_char_p(cmp.o.image),C.byref(cmp.env))
        cmp.compare()


def test_gpio_all_pin_configs_and_input_output_operations(lib):
    rng=random.Random(0x7f58)
    for pin in range(25):
        cmp=Comparison(lib,register_values(pin))
        for mode in (0,1,2):
            for pull in (0,1,2,255):
                for flags in (0,2,0xffffffff):
                    cfg=bytearray(rng.randbytes(12));cfg[4]=mode;cfg[5]=pull
                    cfg[7]=rng.choice([0,1,255]);struct.pack_into('<I',cfg,8,flags)
                    cmp.run(0x7f58,pin,cfg=bytes(cfg))
        for level in (0,1,0xffffffff):cmp.run(0x8054,pin,level)
        cmp.run(0x80ac,pin)
        for sample in (0,0xffffffff,rng.getrandbits(32)):
            cmp.registers[0x400a1380]=cmp.o.registers[0x400a1380]=sample
            cmp.run(0x80f8,pin)


def test_gpio_interrupt_enable_disable_and_callback_dispatch(lib):
    rng=random.Random(0x8148)
    for pin in range(25):
        cmp=Comparison(lib,register_values(pin))
        for edge in (0,1,2,3,255):
            for fn in (0,0x10021,0x10025):
                cmp.run(0x8148,pin,edge,fn,rng.getrandbits(32))
                physical=cmp.state.raw[0x170+pin*8]
                for group,pending in ((0,physical+1),(1,physical+1),(1,0),(1,33)):
                    cmp.registers[0x40401130]=cmp.o.registers[0x40401130]=group
                    cmp.registers[0x400a1020]=cmp.o.registers[0x400a1020]=pending
                    cmp.run(0x8258,returns=False)
                cmp.run(0x81f8,pin,returns=False)


def test_reset_reason_cache_and_enum_lookup(lib):
    for cached in range(256):
        registers=register_values(cached)
        cmp=Comparison(lib,registers)
        cmp.o.put(0x20000254,bytes([cached]));C.memset(C.addressof(cmp.state)+0x254,cached,1)
        cmp.run(0x7c08)
        cmp.run(0x7bfc)
        cmp.registers[0x400b0220]=cmp.o.registers[0x400b0220]=0xffffffff
        cmp.run(0x7c08)
        cmp.run(0x7c3c,cached)
        cmp.run(0x7a54,cached)


def test_gpio_register_reads_fail_without_explicit_model_values():
    o=MSPM0CoreOracle({})
    with pytest.raises(ValueError,match='Unmodelled register'):
        o.call(0x80f8,0)
