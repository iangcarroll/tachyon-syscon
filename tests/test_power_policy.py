import ctypes as C
import random
import struct
import pytest
from power_policy_oracle import PowerPolicyOracle,DEPENDENCIES
from unicorn.arm_const import UC_ARM_REG_R1

CALL=C.CFUNCTYPE(C.c_uint64,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint32)
class Environment(C.Structure):
    _fields_=[('call',CALL),('ctx',C.c_void_p)]

@pytest.fixture
def policy_lib(lib):
    lib.syscon_power_policy_execute.argtypes=[C.c_void_p,C.POINTER(Environment),C.c_uint32,C.c_uint32]
    lib.syscon_power_policy_execute.restype=C.c_uint64
    return lib

def compare(lib,entry,argument=0,initial=None,responses=None):
    responses=responses or {}
    def respond(address,args):return responses.get((address,args),responses.get(address,0))&0xffffffffffffffff
    o=PowerPolicyOracle(respond)
    if initial is not None:o.put(0x20000000,initial)
    state=C.create_string_buffer(bytes(o.cpu.mem_read(0x20000000,4096)),4096)
    events=[]
    def callback(_,address,a,b,payload,length):
        if address in [0x7c54,0x386c]:args=(a,);data=C.string_at(payload,length)
        elif address in [PowerPolicyOracle.PRINT,0x8fa0]:args=(a,b);data=C.string_at(payload,length)
        else:args=(a,b)[:DEPENDENCIES[address]];data=b''
        events.append((address,args,data))
        return respond(address,args)
    cb=CALL(callback);env=Environment(cb,None)
    expected=o.call(entry,argument)
    if entry==0x5638:expected|=o.cpu.reg_read(UC_ARM_REG_R1)<<32
    actual=lib.syscon_power_policy_execute(state,C.byref(env),entry,argument)
    if entry in [0x54cc,0x55c4,0x562c,0x5638,0x5670,0x567c]:assert actual==expected,(entry,actual,expected)
    assert state.raw[:0x800]==bytes(o.cpu.mem_read(0x20000000,0x800)),hex(entry)
    assert events==o.events,(hex(entry),events,o.events)
    return state.raw


def test_power_policy_minimum_voltage_signed_boundaries(policy_lib):
    values=[0,1,1699,1700,3000,3001,0x7ffffffe,0x7fffffff,0x80000000,0xffffffff]
    for previous in values:
        for current in values:
            initial=bytearray(4096);struct.pack_into('<I',initial,0x5c,previous)
            updated=compare(policy_lib,0x559c,initial=initial,responses={0x4c50:current})
            compare(policy_lib,0x55c4,initial=updated)
        reset=compare(policy_lib,0x55b4,initial=initial)
        compare(policy_lib,0x55c4,initial=reset)


def test_power_policy_fault_reason_zero_truncation_and_timestamps(policy_lib):
    rng=random.Random(0x55dc)
    for reason in [0,1,2,7,255,256,257]:
        for now in [0,1,0xffffffff,0x100000000,0xffffffffffffffff]:
            initial=bytearray(rng.randbytes(0x800))+bytearray(0x800)
            updated=compare(policy_lib,0x55dc,reason,initial=initial,responses={0x77b4:now})
            for entry in [0x562c,0x5670,0x567c]:compare(policy_lib,entry,initial=updated)


def test_power_policy_elapsed_and_five_minute_stale_boundaries(policy_lib):
    for start in [0,1,1000,0xfffffffe,0x100000001,0xfffffffffffffff0]:
        for delta in [-1,0,1,299998,299999,300000,300001,0x100000000]:
            now=(start+delta)&0xffffffffffffffff
            for reason in [0,1,255]:
                for stale in [0,1,255]:
                    initial=bytearray(4096);initial[0x36f]=reason;initial[0x380]=stale
                    struct.pack_into('<Q',initial,0x388,start)
                    compare(policy_lib,0x5638,initial=initial,responses={0x77b4:now})
                    updated=compare(policy_lib,0x5694,initial=initial,responses={0x77b4:now})
                    compare(policy_lib,0x567c,initial=updated)


def test_power_policy_report_thresholds_and_dependency_order(policy_lib):
    rng=random.Random(0x5358)
    voltages=[-1,0,1699,1700,1701,2999,3000,3001,4498,4499,4500,4501]
    for iteration in range(180):
        responses={(0x4c50,(pin,)):rng.choice(voltages) for pin in [12,13,14,15,16]}
        responses.update({address:rng.randrange(3) for address in [0x4ca8,0x5af0,0x4d00,0x4d9c]})
        responses.update({address:rng.choice([0,1,2,255]) for address in [0x4d58,0x3620,0x4ec4]})
        responses[0x4df4]=rng.randrange(2)
        compare(policy_lib,0x5358,PowerPolicyOracle.PRINT|1,responses=responses)


def test_power_policy_initialization_payloads_and_ignored_failures(policy_lib):
    for configure in [0,1,2,255,0xffffffff]:
        for failure in [0,1,0xffffffff]:
            compare(policy_lib,0x54cc,configure,responses={0x7c54:failure,0x386c:failure})
