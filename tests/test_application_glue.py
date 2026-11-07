import ctypes as C
import pytest
from test_config_commands import Pipeline
from test_config_updates import image,Store
from config_oracle import FirmwareAssertion
from test_mspm0_core import Comparison,register_values,Environment
from test_uart import setup,IO
from uart_oracle import BASES
from oracle import Oracle

@pytest.mark.parametrize('failure',[None,('program',1),('erase',1),('program',9)])
def test_both_namespace_initializations_and_reload_are_ordered(lib,failure):
    p=Pipeline(lib,b'\xff'*1024,b'\xff'*1024,fail=failure)
    lib.syscon_configuration_init.argtypes=[C.POINTER(Store),C.POINTER(Store),C.c_void_p]
    asserted=False
    try:p.oracle.call(0x30f0)
    except FirmwareAssertion:asserted=True
    result=lib.syscon_configuration_init(C.byref(p.identity.store),C.byref(p.config.store),p.context.runtime)
    assert result==(-1 if asserted else 0)
    assert p.config.contents()==bytes(p.oracle.cpu.mem_read(0xfc00,1024))
    assert p.identity.contents()==bytes(p.oracle.cpu.mem_read(0xf800,1024))
    assert p.flash_events==p.oracle.flash.events
    assert bytes(p.context.runtime)==bytes(p.oracle.cpu.mem_read(0x20000030,22))


def test_app_gpio_setup_through_real_gpio_hal(lib):
    lib.syscon_app_gpio_init.argtypes=[C.c_void_p,C.POINTER(Environment)]
    for seed in range(4):
        p=Comparison(lib,register_values(seed))
        p.o.call(0x4c24)
        lib.syscon_app_gpio_init(p.state,C.byref(p.env))
        p.compare()


def test_uart_vectors_direct_forwarding_and_log_flag(lib):
    o,native,state,io=setup(lib)
    lib.syscon_uart_vector.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(IO)]
    lib.syscon_sg560d_direct.argtypes=[C.c_void_p,C.c_void_p,C.c_uint32,C.POINTER(IO)]
    for port,vector in enumerate([0x8e6c,0x8e7c]):
        for value in [0,1,255,0x12345678]:
            for r in [o.registers,native]:r.values[BASES[port]+0x1020]=11;r.values[BASES[port]+0x1124]=value
            o.call(vector);lib.syscon_uart_vector(state,vector,C.byref(io))
            assert state.raw==o.state();assert native.trace==o.registers.trace
    for data in [b'',b'AT+TEST\r\n',bytes(range(256))]:
        o.put(0x20000900,data);o.call(0x74e8,0x20000900,len(data))
        lib.syscon_sg560d_direct(state,C.c_char_p(data),len(data),C.byref(io))
        assert native.trace==o.registers.trace
    ram=C.create_string_buffer(4096)
    for value in [0,1,2,255,256,0xffffffff]:
        o.call(0x8fc0,value);lib.syscon_log_enable(ram,value)
        assert ram.raw[0x80c]==o.cpu.mem_read(0x2000080c,1)[0]
    assert C.c_uint32(lib.syscon_default_action()).value==o.call(0x76f0)
