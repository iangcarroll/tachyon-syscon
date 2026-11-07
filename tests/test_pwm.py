import ctypes as C
import random
import struct
import pytest
from pwm_oracle import PwmOracle

READ=C.CFUNCTYPE(C.c_uint32,C.c_void_p,C.c_uint32)
WRITE=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32,C.c_uint32)
ASSERT=C.CFUNCTYPE(None,C.c_void_p,C.c_uint)
class Io(C.Structure):
    _fields_=[('context',C.c_void_p),('read',READ),('write',WRITE),('assertion',ASSERT)]

class Pair:
    def __init__(self,lib,registers=None):
        self.lib=lib
        self.original=PwmOracle(registers)
        self.registers=dict(registers or {})
        self.trace=[]
        self.board=C.create_string_buffer(236)
        lib.syscon_pwm_default_board(self.board)
        assert self.board.raw==bytes(self.original.cpu.mem_read(self.original.BOARD,236))
        def read(_,address):
            value=self.registers.get(address,0)
            self.trace.append(('read',address,4,value));return value
        def write(_,address,value):
            self.trace.append(('write',address,4,value));self.registers[address]=value
        self.io=Io(None,READ(read),WRITE(write),ASSERT(lambda _,line:self.trace.append(('assert',line))))
        for name in ('init','write'):
            getattr(lib,'syscon_pwm_'+name).argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint] if name=='write' else [C.c_void_p,C.c_void_p,C.c_uint]

    def check(self):
        assert self.trace==self.original.trace
        assert self.registers==self.original.registers

    def invoke(self,name,address,*args):
        expected=self.original.invoke(address,*args)
        actual=getattr(self.lib,'syscon_pwm_'+name)(self.board,C.byref(self.io),*args)
        assert C.c_uint32(actual).value==expected
        self.check()


def test_pwm_init_shared_timer_order_enable_state_and_writes(lib):
    rng=random.Random(0x87dc)
    for enabled in (0,1,0xfffffffe,0xffffffff):
        registers={base+offset:rng.getrandbits(32) for base in (0x40084000,0x40088000)
                   for offset in (0x1804,0x1830,0x1834,0x1870,0x1874,0x1880,0x1884)}
        for base in (0x40084000,0x40088000): registers[base+0x800]=enabled
        p=Pair(lib,registers)
        for pin in (3,2,1,3,1,2):
            p.invoke('init',0x87dc,pin)
            for value in (0,1,127,255,256,0xffffffff,rng.getrandbits(32)):
                p.invoke('write',0x88c0,pin,value)


def test_pwm_pin_mapping_failures_stop_at_assertion(lib):
    p=Pair(lib)
    for pin in (0,4,24,25,255,256,0xffffffff):
        p.invoke('init',0x87dc,pin)
        p.invoke('write',0x88c0,pin,123)
    # A corrupted board descriptor can match PWM while having no GPIO record.
    p.board[0]=b'\x19'
    p.original.put(p.original.BOARD,b'\x19')
    p.invoke('init',0x87dc,25)


def test_pwm_configure_driver_all_modes_and_mask_preservation(lib):
    rng=random.Random(0x948c)
    base=0x40080000
    for mode in (0,0x20,1,255):
        for extra in (0,1,255):
            for period in (0,1,256,0xffffffff):
                registers={base+offset:rng.getrandbits(32) for offset in range(0x1800,0x1890,4)}
                p=Pair(lib,registers)
                config=struct.pack('<IBBBB',period,mode,extra,rng.randrange(256),rng.randrange(256))
                p.original.put(0x20000900,config)
                p.original.invoke(0x948c,base,0x20000900)
                lib.syscon_pwm_configure(C.byref(p.io),base,C.c_char_p(config))
                p.check()


def test_pwm_low_level_driver_helpers_with_random_fields(lib):
    rng=random.Random(0x9400)
    p=Pair(lib,{0x40080000+offset:rng.getrandbits(32) for offset in range(0x1800,0x1890,4)})
    for _ in range(200):
        a,b=rng.getrandbits(32),rng.getrandbits(32)
        index=rng.randrange(4)
        for name,address,args in [('capture',0x942c,(a,b,index)),('output',0x9470,(a,b,index)),
                                  ('action',0x9450,(a,index)),('compare',0x941c,(a,index))]:
            p.original.invoke(address,0x40080000,*args)
            getattr(lib,'syscon_pwm_'+name)(C.byref(p.io),0x40080000,*args)
            p.check()
    for _ in range(50):
        config=rng.randbytes(3)
        p.original.put(0x20000900,config)
        p.original.invoke(0x9400,0x40080000,0x20000900)
        lib.syscon_pwm_clock(C.byref(p.io),0x40080000,C.c_char_p(config))
        p.check()
