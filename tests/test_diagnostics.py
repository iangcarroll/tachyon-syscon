import ctypes as C
import random
import struct
from unicorn.arm_const import UC_ARM_REG_R1
from oracle import Oracle

CALL=C.CFUNCTYPE(C.c_uint64,C.c_void_p,C.c_uint32,C.c_uint32)
LOG=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32,C.POINTER(C.c_uint32),C.c_char_p)
class IO(C.Structure):_fields_=[('ctx',C.c_void_p),('call',CALL),('log',LOG)]

def test_diagnostics_clock_wrap_rate_temperature_and_sampling_order(lib):
    rng=random.Random(0x3488)
    lib.syscon_diagnostics_poll.argtypes=[C.c_void_p,C.POINTER(IO)]
    for case in range(350):
        o=Oracle();events=[];native=[]
        now=rng.choice([0,5000,5001,6000,0xffffffff,0x100000001,0xffffffffffffffff])
        times=[now,(now+rng.randrange(3))&0xffffffffffffffff,(now+3)&0xffffffffffffffff]
        ot=times[:];nt=times[:]
        o.put(0x200002c0,struct.pack('<QII',rng.choice([0,1,10,0xffffffffffffffff]),rng.choice([0,5000,0xfffffff0]),rng.choice([0,5000,0xffffffff])))
        o.put(0x20000046,bytes([rng.choice([0,1,255])]))
        temperature=rng.choice([-2147483648,-2147483647,-11,-10,-9,-1,0,1,9,10,300,2147483647])&0xffffffff
        results={0x80f8:rng.randrange(3),0x7d54:temperature,0x6690:rng.randrange(4),0x55c4:rng.getrandbits(32)}
        voltages={i:rng.getrandbits(32) for i in [12,13,14,15,16]}
        def result(address,a,clock):return clock.pop(0) if address==0x77b4 else voltages[a] if address==0x4c50 else results[address]
        def dep(cpu,address,argc):
            a=cpu.arg(0) if argc else 0;v=result(address,a,ot);events.append(('call',address,a))
            if address==0x77b4:cpu.cpu.reg_write(UC_ARM_REG_R1,v>>32)
            return v&0xffffffff
        for address,argc in [(0x77b4,0),(0x4c50,1),(0x80f8,1),(0x7d54,0),(0x6690,0),(0x55c4,0)]:
            o.hooks[address]=lambda cpu,address=address,argc=argc:dep(cpu,address,argc)
        def log(cpu):
            fmt=cpu.arg(2);values=[cpu.arg(i) for i in range(3,9)];text=None
            if fmt==0xb295:text=cpu.cstring(values[4]);values[4]=0
            events.append(('log',fmt,values,text))
        o.hooks[0x8f88]=log
        state=C.create_string_buffer(bytes(o.cpu.mem_read(0x20000000,4096)),4096)
        def call(_,address,a):native.append(('call',address,a));return result(address,a,nt)
        io=IO(None,CALL(call),LOG(lambda _,fmt,values,text:native.append(('log',fmt,list(values[:6]),text))))
        o.call(0x3488);lib.syscon_diagnostics_poll(state,C.byref(io))
        assert state.raw[:0x900]==bytes(o.cpu.mem_read(0x20000000,0x900)),case
        assert native==events,(case,native,events)


def test_runtime_accessors_and_hardware_revision_parser(lib):
    rng=random.Random(0x3194);o=Oracle()
    lib.syscon_runtime_get.argtypes=[C.c_void_p,C.c_uint32];lib.syscon_runtime_get.restype=C.c_uint32
    lib.syscon_hwrevision_new.argtypes=[C.c_char_p]
    for _ in range(40):
        state=rng.randbytes(4096);o.put(0x20000000,state)
        for address in [0x3114,0x3120,0x312c,0x3138,0x3144,0x3150,0x315c,0x3178]:
            assert lib.syscon_runtime_get(C.c_char_p(state),address)==o.call(address)
    samples=[b'',b'1.1.0',b'1.2.0',b'2.9.0',b'1.-1.0',b'1.2.3trailer',b' 1. 2. 3',b'1.2',b'1..3',b'1.2.-3',b'1.4294967296.0',b'-4294967295.2.0']
    samples += [f'{rng.randrange(-2,4)}.{rng.randrange(-4,7)}.{rng.randrange(-2,5)}'.encode() for _ in range(100)]
    for s in samples:
        o=Oracle();o.put(0x2000003e,s+b'\0')
        assert lib.syscon_hwrevision_new(s)==o.call(0x3194),s
