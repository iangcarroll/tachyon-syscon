import ctypes as C
import random
import pytest
from i2c_oracle import I2cOracle,I2cRegisterModel,REGISTERS,BASE
from test_adc import Environment,READ,WRITE,SIGNAL

@pytest.fixture
def i2c_lib(lib):
    lib.syscon_i2c_execute.argtypes=[C.c_void_p,C.POINTER(Environment),C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint32]
    lib.syscon_i2c_execute.restype=C.c_uint64
    return lib

def initial_state():
    o=I2cOracle(I2cRegisterModel({}))
    return bytearray(o.cpu.mem_read(0x20000000,4096))

def compare(lib,entry,bus=0,address=0,data=None,length=0,*,registers,scripts=None,irq=None,initial=None):
    original=I2cRegisterModel(registers,scripts,irq);native=I2cRegisterModel(registers,scripts,irq)
    o=I2cOracle(original)
    if initial is not None:o.put(0x20000000,initial)
    state=C.create_string_buffer(bytes(o.cpu.mem_read(0x20000000,4096)),4096)
    native.set_error=lambda:C.memmove(C.addressof(state)+0x760,b'\1',1)
    callbacks=[READ(lambda _,addr:native.read(addr)),WRITE(lambda _,addr,value:native.write(addr,value)),
               SIGNAL(lambda _,cycles:native.delay(cycles)),SIGNAL(lambda _,line:native.assertion(line))]
    env=Environment(*callbacks,None)
    buffer=C.create_string_buffer(data,512) if data is not None else None
    expected=o.invoke(entry,bus,address,data,length)
    actual=lib.syscon_i2c_execute(state,C.byref(env),entry,bus,address,buffer,length)
    if entry!=0x8798:assert actual==expected,(hex(entry),bus,address,length,actual,expected)
    assert state.raw[:0x800]==bytes(o.cpu.mem_read(0x20000000,0x800)),hex(entry)
    assert native.events==original.events,(hex(entry),bus,address,length,native.events[:40],original.events[:40])
    assert native.registers==original.registers
    assert native.scripts==original.scripts
    if entry==0x860c and data is not None:
        assert buffer.raw[:len(data)]==bytes(o.cpu.mem_read(o.DATA,len(data)))
    return state.raw,native.events

def registers(seed=1):
    rng=random.Random(seed)
    r={a:rng.getrandbits(32) for a in REGISTERS}
    r[BASE+0x123c]=0x800
    r[BASE+0x1218]=0
    return r


def test_i2c_initialization_payload_modes_and_irq_masks(i2c_lib):
    rng=random.Random(0x82f0)
    for mode in [0,1,2,255]:
        for irq in [0,24,31,32,127,128,255]:
            state=initial_state();state[0x144]=irq;state[0x761]=rng.randrange(256)
            compare(i2c_lib,0x82f0,data=bytes([mode])+rng.randbytes(7),registers=registers(irq),initial=state)


def test_i2c_assertion_boundaries(i2c_lib):
    for entry in [0x82f0,0x844c,0x860c]:
        for bus in [1,255,256,0xffffffff]:
            compare(i2c_lib,entry,bus,data=b'\0'*8,registers={})
    compare(i2c_lib,0x82f0,registers={})
    for entry in [0x844c,0x860c]:
        for active in [1,2,255]:
            state=initial_state();state[0x761]=active
            compare(i2c_lib,entry,data=b'x',length=1,registers={},initial=state)


def test_i2c_write_fifo_chunking_address_mask_and_zero_length(i2c_lib):
    rng=random.Random(0x844c)
    for length in [0,1,2,7,8,9,15,16,31,128,255]:
        for address in [0,0x20,0x7f,0x3ff,0xffffffff]:
            scripts={BASE+0x1218:([0x20,0x40,0] if length else [0x20,0])}
            compare(i2c_lib,0x844c,address=address,data=rng.randbytes(max(length,1)),length=length,
                    registers=registers(length),scripts=scripts)


def test_i2c_read_fifo_byte_truncation_and_zero_length(i2c_lib):
    rng=random.Random(0x860c)
    for length in [0,1,2,7,8,9,31,128,255]:
        for address in [0,0x20,0x7f,0x3ff,0xffffffff]:
            scripts={BASE+0x1218:[0x20,0x40,0],BASE+0x123c:[1]*length+[0],
                     BASE+0x121c:[rng.getrandbits(32) for _ in range(length)]}
            compare(i2c_lib,0x860c,address=address,data=b'\xa5'*max(length,1),length=length,
                    registers=registers(length),scripts=scripts)


def test_i2c_interrupt_error_latch_and_sticky_transfer_behavior(i2c_lib):
    for reason in [0,1,7,8,9,10,11,12,255,256,264,267]:
        for previous in [0,1,255]:
            r=registers();r[BASE+0x1020]=reason
            state=initial_state();state[0x760]=previous
            compare(i2c_lib,0x8798,registers=r,initial=state)
    for entry in [0x844c,0x860c]:
        for previous in [0,1,255]:
            for injection in [None,(BASE+0x1218,2),(BASE+0x123c,1),(BASE+0x123c,4)]:
                length=12;state=initial_state();state[0x760]=previous
                scripts={BASE+0x1218:[0x20,0x40,0]}
                if entry==0x860c:scripts[BASE+0x123c]=[1]*length+[0x800]
                compare(i2c_lib,entry,address=0x20,data=b'\xa5'*length,length=length,
                        registers=registers(),scripts=scripts,irq=injection,initial=state)


@pytest.mark.parametrize('entry',[0x844c,0x860c])
@pytest.mark.parametrize('phase',['idle','start','fifo','finish'])
def test_i2c_bounded_wait_timeouts_and_cleanup(i2c_lib,entry,phase):
    r=registers();scripts={}
    if phase=='start':scripts[BASE+0x1218]=[0x20]+[0]*10000
    elif phase=='fifo':
        scripts[BASE+0x1218]=[0x20,0x40]
        scripts[BASE+0x123c]=[0]*(10001 if entry==0x844c else 10000)+[0x800]
    elif phase=='finish':
        scripts[BASE+0x1218]=[0x20,0x40]+[0x40]*10000
        if entry==0x860c:scripts[BASE+0x123c]=[1]+[0x800]
    compare(i2c_lib,entry,address=0x20,data=b'x',length=1,registers=r,scripts=scripts)


def test_i2c_fifo_helper_short_write_still_advances_outer_count(i2c_lib):
    # Outer says8slotsavailable, helperseesnone andwritesnothing. Original still
    # increments its intendedcount andreturns8; preservethis observable quirk.
    compare(i2c_lib,0x844c,address=0x20,data=b'abcdefgh',length=8,registers=registers(),
            scripts={BASE+0x1218:[0x20,0x40,0],BASE+0x123c:[0x800,0,0x800]})


def test_i2c_large_transfer_counter_wrap_terminated_by_irq(i2c_lib):
    for length in [256,257,65536]:
        for entry in [0x844c,0x860c]:
            scripts={BASE+0x1218:[0x20,0x40,0]}
            injection=(BASE+0x123c,40)
            if entry==0x860c:scripts[BASE+0x123c]=[1]*40+[0x800]
            compare(i2c_lib,entry,address=0x20,data=b'\xa5'*256,length=length,
                    registers=registers(),scripts=scripts,irq=injection)


def test_i2c_original_nonprogress_for_256_byte_write_without_irq():
    model=I2cRegisterModel(registers(),{BASE+0x1218:[0x20,0x40]})
    o=I2cOracle(model);o.put(o.DATA,b'\xa5'*256)
    with pytest.raises(RuntimeError,match='Instruction budget exhausted'):
        o.call(0x844c,0,0x20,o.DATA,256,count=10000)
    assert sum(event==('write',0x400b040c,10) for event in model.events)>10
    assert not any(event[0]=='write' and event[1]==BASE+0x1220 for event in model.events)
