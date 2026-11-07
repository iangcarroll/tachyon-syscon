import ctypes as C
import random
import struct
import pytest
from adc_oracle import AdcOracle,RegisterModel,REGISTERS,ADC,VREF

READ=C.CFUNCTYPE(C.c_uint32,C.c_void_p,C.c_uint32)
WRITE=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32,C.c_uint32)
SIGNAL=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32)
class Environment(C.Structure):
    _fields_=[('read32',READ),('write32',WRITE),('delay',SIGNAL),('assertion',SIGNAL),('ctx',C.c_void_p)]

@pytest.fixture
def adc_lib(lib):
    lib.syscon_adc_execute.argtypes=[C.c_void_p,C.POINTER(Environment),C.c_uint32,C.c_uint32,C.c_void_p]
    lib.syscon_adc_execute.restype=C.c_uint64
    return lib

def compare(lib,entry,pin=0,config=None,*,registers,scripts=None,initial=None):
    original=RegisterModel(registers,scripts);native=RegisterModel(registers,scripts)
    o=AdcOracle(original)
    if initial is not None:o.put(0x20000000,initial)
    state=C.create_string_buffer(bytes(o.cpu.mem_read(0x20000000,4096)),4096)
    callbacks=[READ(lambda _,addr:native.read(addr)),WRITE(lambda _,addr,value:native.write(addr,value)),
               SIGNAL(lambda _,cycles:native.delay(cycles)),SIGNAL(lambda _,line:native.assertion(line))]
    env=Environment(*callbacks,None)
    expected=o.invoke(entry,pin,config)
    actual=lib.syscon_adc_execute(state,C.byref(env),entry,pin,C.c_char_p(config) if config is not None else None)
    assert actual==expected,(hex(entry),pin,config,actual,expected)
    assert state.raw[:0x800]==bytes(o.cpu.mem_read(0x20000000,0x800)),hex(entry)
    assert native.events==original.events,(hex(entry),pin,native.events,original.events)
    assert native.registers==original.registers
    assert native.scripts==original.scripts
    return state.raw,native.events

def initial_state():
    o=AdcOracle(RegisterModel({}))
    return bytearray(o.cpu.mem_read(0x20000000,4096))


def test_adc_init_all_pins_and_arbitrary_configuration_payload(adc_lib):
    rng=random.Random(0x7c54)
    for pin in [12,13,14,15,16,23,268,279]:
        for _ in range(12):
            registers={a:rng.getrandbits(32) for a in REGISTERS}
            config=rng.randbytes(7)
            compare(adc_lib,0x7c54,pin,config,registers=registers)


def test_adc_invalid_pin_and_null_config_assertion_boundaries(adc_lib):
    for pin in [0,1,11,17,22,24,255,256,0xffffffff]:
        for entry in [0x7c54,0x7e7c,0x7f24]:
            compare(adc_lib,entry,pin,b'\0'*7,registers={})
    compare(adc_lib,0x7c54,12,registers={})


def test_adc_raw_channel_selection_and_signed_fixed_point_wrapping(adc_lib):
    rng=random.Random(0x7f24)
    for _ in range(320):
        pin=rng.choice([12,13,14,15,16,23])
        registers={a:rng.getrandbits(32) for a in REGISTERS}
        state=initial_state()
        for slot in range(6):
            state[0xf4+slot*12+8]=rng.randrange(32)
            state[0xf4+slot*12+9]=rng.randrange(4)
        struct.pack_into('<I',state,0x68c,rng.choice([0,1,1800,65535,0x7fffffff,0x80000000,rng.getrandbits(32)]))
        compare(adc_lib,0x7e7c,pin,registers=registers,initial=state)
        compare(adc_lib,0x7f24,pin,registers=registers,initial=state)


def test_adc_temperature_reference_ready_timeout_and_final_recheck(adc_lib):
    rng=random.Random(0x7d54)
    for initialized in [0,1,255]:
        for ready_after in [0,1,2,99,100,101]:
            registers={a:rng.getrandbits(32) for a in REGISTERS}
            registers[VREF+0x1104]=0;registers[0x41c4003c]=1500
            script=[0]*ready_after+[1,1]
            state=initial_state();state[0x694]=initialized
            compare(adc_lib,0x7d54,registers=registers,scripts={VREF+0x1104:script},initial=state)
        registers[VREF+0x1104]=0
        compare(adc_lib,0x7d54,registers=registers,initial=state)


def test_adc_temperature_calibration_invalid_and_signed_division(adc_lib):
    rng=random.Random(0x7168)
    values=[0,1,0xfff,0x1000,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
    values += [rng.getrandbits(32) for _ in range(100)]
    for calibration in values:
        registers={a:rng.getrandbits(32) for a in REGISTERS}
        registers[VREF+0x1104]=1;registers[0x41c4003c]=calibration
        state=initial_state();state[0x694]=1
        compare(adc_lib,0x7d54,registers=registers,initial=state)


def test_adc_missing_register_input_fails_closed():
    o=AdcOracle(RegisterModel({}))
    with pytest.raises(AssertionError,match='Unprovided register'):
        o.invoke(0x7e7c,12)
