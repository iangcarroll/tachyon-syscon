import ctypes as C
import random
import pytest
from ioexpander_oracle import IoOracle, RegisterBus

INIT=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint,C.c_void_p)
TRANSFER=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_uint)
NOTIFY=C.CFUNCTYPE(None,C.c_void_p,C.c_uint)
GPIO_READ=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint)
GPIO_WRITE=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint)

class Context(C.Structure):
    _fields_=[('context',C.c_void_p),('init',INIT),('write',TRANSFER),('read',TRANSFER),
              ('assertion',NOTIFY),('invalid',NOTIFY),('gpio_read',GPIO_READ),
              ('gpio_write',GPIO_WRITE),('initialized',C.c_uint8)]


class Pair:
    def __init__(self, lib, registers, initialized=1):
        self.lib=lib
        self.native=RegisterBus(registers)
        self.original=RegisterBus(registers)
        self.oracle=IoOracle(self.original,initialized)
        def read(_,bus,address,buf,count):
            result,value=self.native.read(bus,address,count)
            if result==count: C.memmove(buf,value,count)
            return result
        self.ctx=Context(None,
            INIT(lambda _,bus,cfg:self.native.init(bus,C.string_at(cfg,8))),
            TRANSFER(lambda _,bus,address,buf,count:self.native.write(bus,address,C.string_at(buf,count))),
            TRANSFER(read),NOTIFY(lambda _,line:self.native.assertion(line)),
            NOTIFY(lambda _,pin:self.native.invalid(pin)),
            GPIO_READ(lambda _,pin:self.native.gpio_read(pin)),
            GPIO_WRITE(lambda _,pin,value:self.native.gpio_write(pin,value)),initialized)
        for name in ('write16','write8','read8','reset','init','configure','write','read'):
            getattr(lib,'syscon_io_'+name).restype=C.c_int

    def inject(self,kind,results):
        self.native.results[kind].extend(results)
        self.original.results[kind].extend(results)

    def check(self):
        assert self.native.events==self.original.events
        assert self.native.registers==self.original.registers
        assert self.native.pointer==self.original.pointer
        assert self.ctx.initialized==self.oracle.cpu.mem_read(self.oracle.INITIALIZED,1)[0]

    def simple(self,name,address,*args,compare_result=True):
        expected=self.oracle.invoke(address,*args)
        actual=getattr(self.lib,name)(C.byref(self.ctx),*args)
        if compare_result or expected==-2: assert actual==expected
        self.check()

    def configure(self,pin,config):
        ptr=0x20000900 if config is not None else 0
        if ptr: self.oracle.put(ptr,config)
        expected=self.oracle.invoke(0x386c,pin,ptr)
        actual=self.lib.syscon_io_configure(C.byref(self.ctx),pin,C.c_char_p(config))
        assert actual==expected
        self.check()

    def read(self,pin):
        self.oracle.put(0x20000900,b'\xa5')
        value=C.c_uint8(0xa5)
        expected=self.oracle.invoke(0x39e8,pin,0x20000900)
        actual=self.lib.syscon_io_read(C.byref(self.ctx),pin,C.byref(value))
        assert actual==expected
        assert value.value==self.oracle.cpu.mem_read(0x20000900,1)[0]
        self.check()


def test_ioexpander_random_operations_and_all_pins(lib):
    rng=random.Random(0x386c)
    p=Pair(lib,rng.randbytes(256))
    for pin in range(16):
        for output in (0,1,2,255):
            for initial in (0,1,2,255):
                for apply in (0,1,255):
                    p.configure(pin,bytes([output,initial,apply]))
                    p.read(pin)
                    p.simple('syscon_io_write',0x3940,pin,rng.choice([0,1,2,255,0xffffffff]))
    for _ in range(500):
        pin=rng.randrange(16)
        if rng.randrange(2): p.configure(pin,rng.randbytes(3))
        else: p.simple('syscon_io_write',0x3940,pin,rng.randrange(2))
        p.read(pin)


@pytest.mark.parametrize('reset',[0,1,2,0xffffffff])
def test_ioexpander_init_and_reset_sequence(lib,reset):
    p=Pair(lib,bytes(range(256)),initialized=0)
    p.inject('init',[-1,1,2])
    p.inject('write',[0,1,-1])
    p.simple('syscon_io_init',0x3808,reset)
    p.simple('syscon_io_reset',0x37e4,compare_result=False)


@pytest.mark.parametrize('kind,count', [('write',1),('write',2),('write',3),('read',1),('init',0)])
@pytest.mark.parametrize('failures', [0,1,2,3,4])
def test_ioexpander_retry_success_and_terminal_assertion(lib,kind,count,failures):
    p=Pair(lib,bytes(range(256)),initialized=0 if kind=='init' else 1)
    bad_results=[-1, count+1, -123, count-1] if kind!='init' else [-1,1,2,3]
    p.inject(kind,bad_results[:failures])
    if kind=='init': p.simple('syscon_io_init',0x3808,0)
    elif kind=='write' and count>1:
        name,addr=('write8',0x374c) if count==2 else ('write16',0x3668)
        p.simple('syscon_io_'+name,addr,4,0x1234,compare_result=False)
    else:
        value=C.c_uint8(0xa5)
        p.oracle.put(0x20000900,b'\xa5')
        expected=p.oracle.invoke(0x36bc,0,0x20000900)
        actual=lib.syscon_io_read8(C.byref(p.ctx),0,C.byref(value))
        if expected==-2: assert actual==-2
        assert value.value==p.oracle.cpu.mem_read(0x20000900,1)[0]
        p.check()


def test_ioexpander_preconditions_match_assertion_lines(lib):
    for initialized,pin in [(0,0),(0,16),(1,16),(1,0xffffffff)]:
        p=Pair(lib,bytes(256),initialized)
        p.configure(pin,b'\1\0\1')
        p.simple('syscon_io_write',0x3940,pin,1)
        p.read(pin)
    Pair(lib,bytes(256)).configure(0,None)


def test_gpio_routing_and_byte_truncation(lib):
    p=Pair(lib,bytes(range(256)))
    for pin in [*range(41),41,255,256,280,281,296,0xffffffff]:
        p.simple('syscon_gpio_read',0x3620,pin)
        p.simple('syscon_gpio_write',0x364e,pin,0xffffffff,compare_result=False)


@pytest.mark.parametrize('successful_writes',[0,1,2])
def test_ioexpander_failed_reset_does_not_mark_initialized(lib,successful_writes):
    p=Pair(lib,bytes(range(256)),initialized=0)
    p.inject('write',[3]*successful_writes+[-1]*4)
    p.simple('syscon_io_init',0x3808,1)
    assert p.ctx.initialized==0


def test_ioexpander_read_and_write_retry_budgets_are_independent(lib):
    p=Pair(lib,bytes(range(256)))
    p.inject('write',[-1,0,2])
    p.inject('read',[0,2,-1])
    p.read(0)
