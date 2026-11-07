import ctypes as C
import copy
import random
import struct
import pytest
from power_oracle import PowerOracle,PowerEnvironment,PowerAssertion

CALL=C.CFUNCTYPE(C.c_uint64,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint32)
class Env(C.Structure): _fields_=[('call',CALL),('ctx',C.c_void_p)]

class Pair:
    def __init__(self,lib):
        self.lib=lib;self.o=PowerOracle();self.native=PowerEnvironment()
        self.state=C.create_string_buffer(bytes(self.o.cpu.mem_read(0x20000000,4096)),4096)
        self.cb=CALL(lambda _,f,a,b,p,n:self.native.call(f,a,b,C.string_at(p,n) if n else b''))
        self.env=Env(self.cb,None)
        lib.syscon_power_execute.argtypes=[C.c_void_p,C.POINTER(Env),C.c_uint32,C.c_uint32]
        lib.syscon_power_execute.restype=C.c_uint64
    def sync(self): self.native=copy.deepcopy(self.o.env)
    def write_state(self,offset,data):
        self.o.put(0x20000000+offset,data);C.memmove(C.addressof(self.state)+offset,data,len(data))
    def step(self,entry,a=0,has_return=True):
        self.o.env.trace.clear();self.native.trace.clear()
        asserted=False
        try: expected=self.o.call(entry,a)
        except PowerAssertion: asserted=True;expected=0xffffffffffffffff
        actual=self.lib.syscon_power_execute(self.state,C.byref(self.env),entry,a)
        if asserted or has_return: assert actual==expected,(hex(entry),a,actual,expected)
        assert self.native.trace==self.o.env.trace,(hex(entry),a,self.native.trace,self.o.env.trace)
        assert self.native.gpio==self.o.env.gpio
        assert self.state.raw[:0x900]==bytes(self.o.cpu.mem_read(0x20000000,0x900)),hex(entry)


def test_adc_scaling_zero_retry_and_pin_truncation(lib):
    p=Pair(lib)
    for pin in [0,12,13,14,15,16,23,24,0x1000c,0xffffffff]:
        for samples in [[0],[0,1000],[1],[1499],[0xffffffff]]:
            p.o.env.adc[pin&0xffff]=samples[:];p.sync();p.step(0x4c50,pin)


def test_power_selectors_routing_and_failure_assertions(lib):
    p=Pair(lib);rng=random.Random(0x4e34)
    entries=[0x4ca8,0x4d00,0x4d9c,0x4d58,0x4df4,0x4ec4,
             0x4d68,0x4e04,0x4ed4,0x5264,0x4e34,0x4ee0,0x4fd0,0x5004,0x5048]
    void={0x4d68,0x4e04,0x4ed4,0x5264}
    for _ in range(1000):
        for pin in [25,26,28,32,33,34,35,36,37,38,40]:p.o.env.gpio[pin]=rng.randrange(2)
        p.o.env.stuck={rng.choice([25,26,33,34,35,40])} if rng.randrange(3)==0 else set()
        p.o.env.write_result=rng.choice([0,0,-1])
        entry=rng.choice(entries);a=rng.randrange(3)
        if entry==0x4e04:a&=1 # Log string lookup is only defined for0/1.
        p.sync();p.step(entry,a,entry not in void)


def test_usb_recovery_cooldown_submission_and_task_callbacks(lib):
    p=Pair(lib)
    for now in [0,1,1999,2000,2001,0xffffffff,0x100000000,0xffffffffffffffff]:
        for started in [0,1,(now-1999)&0xffffffffffffffff,(now-2000)&0xffffffffffffffff]:
            p.write_state(0x378,struct.pack('<Q',started))
            for pending in [0,1,255]:
                p.write_state(0x370,bytes([pending]));p.o.env.now=now;p.sync();p.step(0x517c)
    for voltage in [0,562,563,1500]:
        for enabled in [0,1]:
            for result in [0,-1,1]:
                p.write_state(0x370,b'\0');p.write_state(0x378,b'\0'*8)
                p.o.env.adc[16]=[voltage];p.o.env.gpio[37]=enabled
                p.o.env.task_result=result;p.sync();p.step(0x51c0)
                p.step(0x5148);p.step(0x50f4)


def test_battery_detection_routes_and_voltage_boundaries(lib):
    p=Pair(lib)
    for battery in [0,999,1000,1001]:
        for detect in [0,399,400,401,1199,1200,1201,0xffffffff]:
            p.o.env.gpio[33]=p.o.env.gpio[34]=0
            p.o.env.adc[14]=[battery];p.o.env.adc[23]=[detect]
            p.sync();p.step(0x5274)


def test_usb_recovery_through_real_scheduler_and_callbacks(lib):
    ACTION=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32)
    lib.syscon_tasks_submit.argtypes=[C.c_void_p,C.c_void_p,C.c_uint]
    lib.syscon_tasks_poll.argtypes=[C.c_void_p,C.c_uint64,ACTION,C.c_void_p]
    for epoch in [1,0xfffffff0]:
        p=Pair(lib)
        p.o.env.gpio[37]=1;p.o.env.adc[16]=[563];p.o.env.now=epoch;p.sync()
        del p.o.hooks[0x7554] # Execute the actual original task scheduler.
        tasks=C.c_void_p(C.addressof(p.state)+0x534)
        p.o.call(0x7540);lib.syscon_tasks_init(tasks)
        environment_call=p.native.call
        def call(address,a=0,b=0,payload=b''):
            if address==0x7554:
                return lib.syscon_tasks_submit(tasks,C.c_char_p(payload),b)&0xffffffff
            return environment_call(address,a,b,payload)
        p.native.call=call
        callback=ACTION(lambda _,address:lib.syscon_power_execute(p.state,C.byref(p.env),address&~1,0))
        p.step(0x51c0)
        for elapsed in [0,1,2,100,250,251,252,253,254,2000,2252,2253]:
            now=(epoch+elapsed)&0xffffffffffffffff
            p.o.env.now=p.native.now=now
            p.o.env.trace.clear();p.native.trace.clear()
            p.o.call(0x75d8)
            lib.syscon_tasks_poll(tasks,now,callback,None)
            assert p.state.raw[:0x900]==bytes(p.o.cpu.mem_read(0x20000000,0x900))
            assert p.native.gpio==p.o.env.gpio
            # C scheduler receives its timestamp as an argument; compare side effects.
            effects=lambda e:[event for event in e.trace if event[0]!=0x77b4]
            assert effects(p.native)==effects(p.o.env)
            p.step(0x517c)
