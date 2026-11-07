import ctypes as C
import random
import struct
import pytest
from rgb_oracle import RgbOracle

PWM_INIT=C.CFUNCTYPE(None,C.c_void_p,C.c_uint)
PWM_WRITE=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint)
REGISTER=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint,C.c_uint,C.c_uint32,C.c_uint32)
NOTIFY=C.CFUNCTYPE(None,C.c_void_p)

class Io(C.Structure):
    _fields_=[('context',C.c_void_p),('pwm_init',PWM_INIT),('pwm_write',PWM_WRITE),
              ('timer_register',REGISTER),('timer_init',NOTIFY),('timer_error',NOTIFY)]

class Pair:
    def __init__(self,lib,state=bytes(28),timer_result=0):
        self.lib=lib
        self.original=RgbOracle(state,timer_result)
        self.state=C.create_string_buffer(state,28)
        self.events=[]
        def register(_,period,repeat,callback,argument):
            self.events.append(('register',period,repeat,callback,argument))
            return timer_result
        self.io=Io(None,PWM_INIT(lambda _,pin:self.events.append(('pwm-init',pin))),
                   PWM_WRITE(lambda _,pin,value:self.events.append(('pwm-write',pin,value))),
                   REGISTER(register),NOTIFY(lambda _:self.events.append(('timer-init',))),
                   NOTIFY(lambda _:self.events.append(('timer-error',))))

    def check(self):
        assert self.state.raw==self.original.state(),(self.state.raw.hex(),self.original.state().hex())
        assert self.events==self.original.events

    def call(self,name,address,*args,check_return=True):
        expected=self.original.call(address,*args)
        actual=getattr(self.lib,'syscon_rgb_'+name)(self.state,C.byref(self.io),*args)
        if check_return: assert C.c_uint32(actual).value==expected
        self.check()

    def configure(self,config):
        addr=0x20000900 if config is not None else 0
        if addr: self.original.put(addr,config)
        expected=self.original.call(0x5c38,addr)
        actual=self.lib.syscon_rgb_configure(self.state,C.byref(self.io),C.c_char_p(config))
        assert C.c_uint32(actual).value==expected
        self.check()

    def tick(self,count=1):
        for _ in range(count):
            self.call('tick',0x5cac,check_return=False)


@pytest.mark.parametrize('timer_result',[-1,0,3])
def test_rgb_initialization_preserves_adjacent_globals(lib,timer_result):
    p=Pair(lib,bytes(range(28)),timer_result)
    for polarity in [0,1,2,255,256,0xffffffff]:
        p.call('init',0x5b7c,polarity)


@pytest.mark.parametrize('state',range(10))
def test_rgb_presets_and_complete_pattern_cycles(lib,state):
    p=Pair(lib)
    p.call('init',0x5b7c,1)
    p.call('set_state',0x5c68,state,0)
    p.tick(450)


def test_rgb_temporary_state_restore_rounding_and_nesting(lib):
    p=Pair(lib)
    p.call('init',0x5b7c,0)
    p.call('set_state',0x5c68,5,0)
    for duration in [0,1,19,20,21,39,40,59,60,100]:
        p.call('set_state',0x5c68,8,duration)
        p.tick(10)
    p.call('set_state',0x5c68,2,100)
    p.call('set_state',0x5c68,3,40)
    p.tick(50)
    p.call('transient',0x5e24,check_return=False)
    p.tick(5)


def test_rgb_random_configuration_brightness_mode_and_tick_sequences(lib):
    rng=random.Random(0x5cac)
    p=Pair(lib)
    p.call('init',0x5b7c,1)
    p.configure(None)
    for _ in range(500):
        choice=rng.randrange(5)
        if choice==0:
            p.configure(rng.randbytes(3)+bytes([rng.randrange(256),rng.randrange(8)]))
        elif choice==1:
            p.call('brightness',0x5bd4,rng.choice([0,1,99,100,101,255,256,0xffffffff]),rng.randrange(2))
        elif choice==2:
            p.call('pattern',0x5bfc,rng.choice([0,1,2,3,4,5,6,255,256,257,258,0xffffffff]),rng.randrange(2))
        elif choice==3:
            p.call('set_state',0x5c68,rng.randrange(12),rng.randrange(300))
        else: p.tick(rng.randrange(20))


def test_rgb_scaling_all_channels_and_float_conversion_edges(lib):
    rng=random.Random(0x5b20)
    o=RgbOracle()
    lib.syscon_rgb_scale.argtypes=[C.c_void_p,C.c_uint]
    lib.syscon_rgb_scale.restype=C.c_uint8
    bits=[0,0x80000000,1,0x007fffff,0x00800000,0x7f800000,0xff800000,
          0x7fc00000,0xffc00000,0x7f800001,0xff800001,0x4effffff,0x4f000000,0x4f800000]
    bits += [struct.unpack('<I',struct.pack('<f',x))[0] for x in [0.1,0.99,1,1.01,49.999,99.999,100,101,255,256,-0.5,-1,-100]]
    bits += [rng.getrandbits(32) for _ in range(500)]
    for bit_pattern in bits:
        for polarity in (0,1,255):
            state=bytearray(28)
            struct.pack_into('<I',state,8,bit_pattern)
            state[16]=polarity
            o.put(o.STATE,state)
            for channel in [0,1,127,254,255,256,0xffffffff]:
                expected=o.call(0x5b20,channel)
                actual=lib.syscon_rgb_scale(C.c_char_p(bytes(state)),channel)
                assert actual==expected,(hex(bit_pattern),polarity,channel,actual,expected)
    for brightness in range(101):
        state=bytearray(28)
        struct.pack_into('<f',state,8,float(brightness))
        state[16]=1
        o.put(o.STATE,state)
        for channel in range(256):
            assert lib.syscon_rgb_scale(C.c_char_p(bytes(state)),channel)==o.call(0x5b20,channel)


def test_rgb_getters_and_names(lib):
    rng=random.Random(0x5dc8)
    for _ in range(50):
        p=Pair(lib,rng.randbytes(28))
        assert lib.syscon_rgb_get_state(p.state)==p.original.call(0x5dbc)
        for present in (False,True):
            result=C.create_string_buffer(6)
            ptr=0x20000900 if present else 0
            expected=p.original.call(0x5dc8,ptr)
            actual=lib.syscon_rgb_get_config(p.state,result if present else None)
            assert actual==expected
            if present: assert result.raw==bytes(p.original.cpu.mem_read(ptr,6))
    for name,address in [('state_name',0x5df4),('pattern_name',0x5e0c)]:
        fn=getattr(lib,'syscon_rgb_'+name)
        fn.argtypes=[C.c_uint]
        fn.restype=C.c_char_p
        for value in [*range(12),255,256,0xffffffff]:
            assert fn(value)==p.original.cstring(p.original.call(address,value))
