import ctypes as C
from collections import deque
import random
import pytest
from fault_oracle import FaultOracle
from unicorn.arm_const import UC_ARM_REG_PRIMASK

READ=C.CFUNCTYPE(C.c_uint32,C.c_void_p,C.c_uint32)
WRITE=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32,C.c_uint32)
LOG=C.CFUNCTYPE(None,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint32)
VOID=C.CFUNCTYPE(None,C.c_void_p)
CONFIG=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_void_p)
ARG=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32)
BUTTON=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint)
class Io(C.Structure):
    _fields_=[('context',C.c_void_p),('read',READ),('write',WRITE),('log',LOG),('disable',VOID),
              ('configure',CONFIG),('toggle',ARG),('delay',ARG),('watchdog',VOID),('button',BUTTON),('barrier',VOID)]

class Pair:
    def __init__(self,lib,buttons=(),registers=None):
        self.lib=lib
        self.original=FaultOracle(buttons,registers)
        self.buttons=deque(buttons)
        self.events=[]
        self.registers=dict(registers or {})
        def read(_,address):
            value=self.registers.get(address,0);self.events.append(('read',address,value));return value
        def write(_,address,value):
            self.events.append(('write',address,value));self.registers[address]=value
        def button(_,pin):
            value=self.buttons.popleft() if self.buttons else 1
            self.events.append(('gpio-read',pin,value));return value
        self.io=Io(None,READ(read),WRITE(write),
            LOG(lambda _,expr,file,line:self.events.append(('log-assert',1,b'ASRT',b'Assertion failed: %s, fileName %s, line %d (err: %d)',expr,file,line,1))),
            VOID(lambda _:self.events.append(('disable-interrupts',))),
            CONFIG(lambda _,pin,cfg:self.events.append(('gpio-configure',pin,C.string_at(cfg,12)))),
            ARG(lambda _,pin:self.events.append(('gpio-toggle',pin))),ARG(lambda _,count:self.events.append(('delay-cycles',count))),
            VOID(lambda _:self.events.append(('watchdog',))),BUTTON(button),VOID(lambda _:self.events.append(('barrier',))))

    def check(self):
        assert self.events==self.original.events
        assert self.registers==self.original.registers


@pytest.mark.parametrize('buttons',[[],[0,0],[0,1]*20,[1]*19+[0,0],[1]*19+[0,1],[2,-1,1,0,1,0,0]])
def test_assertion_body_led_delays_button_debounce_watchdog_and_reset(lib,buttons):
    p=Pair(lib,buttons,{0xe000e010:0xffffffff})
    p.original.put(0x20000900,b'unit.cpp\0');p.original.put(0x20000940,b'x != 0\0')
    expected=p.original.invoke(0x2678,0x20000900,0x12345678,0x20000940)
    lib.syscon_assertion.argtypes=[C.c_void_p,C.c_char_p,C.c_uint32,C.c_char_p]
    actual=lib.syscon_assertion(C.byref(p.io),b'unit.cpp',0x12345678,b'x != 0')
    assert actual==expected==-1
    assert p.original.cpu.reg_read(UC_ARM_REG_PRIMASK)==1
    p.check()


def test_fault_breadcrumbs_names_clock_and_cached_reason(lib):
    rng=random.Random(0x7b78)
    p=Pair(lib,registers={0x400b0104:rng.getrandbits(32)})
    lib.syscon_fault_stage_name.restype=C.c_char_p
    lib.syscon_fault_stage_name.argtypes=[C.c_uint]
    for value in [*range(24),255,256,0xffffffff]+[rng.getrandbits(32) for _ in range(30)]:
        p.original.invoke(0x7b78,value);lib.syscon_fault_stage_set(C.byref(p.io),value)
        assert lib.syscon_fault_stage_get(C.byref(p.io))==p.original.invoke(0x7b88)
        assert lib.syscon_fault_stage_name(value)==p.original.cstring(p.original.invoke(0x7b9c,value))
        p.check()
    assert lib.syscon_enable_mftick(C.byref(p.io))==p.original.invoke(0x7be0)
    p.check()
    for value in range(256):
        p.original.put(0x20000254,bytes([value]))
        assert lib.syscon_fault_cached_reason(C.c_char_p(bytes([value])))==p.original.invoke(0x7bfc)


@pytest.mark.parametrize('name,address',[('hardfault',0x7bb8),('nmi',0x7bcc)])
def test_hardfault_and_nmi_store_reason_then_halt(lib,name,address):
    p=Pair(lib)
    expected=p.original.invoke(address)
    actual=getattr(lib,'syscon_fault_'+name)(C.byref(p.io))
    assert actual==expected==-2
    p.check()
