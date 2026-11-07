import ctypes as C
import random
import struct
from unicorn.arm_const import UC_ARM_REG_R1
from oracle import Oracle

CALL=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32)


def test_scheduler_against_original_across_wrap_and_callback_failures(lib):
    o=Oracle()
    o.hooks[0x8f88]=lambda _:None
    now=[0]
    original_calls=[]
    native_calls=[]
    returns={0x10021:1,0x10025:0,0x10029:-1}
    def clock(cpu):
        cpu.cpu.reg_write(UC_ARM_REG_R1,now[0]>>32)
        return now[0]&0xffffffff
    o.hooks[0x77b4]=clock
    for address,result in returns.items():
        def callback(cpu,address=address,result=result):
            original_calls.append(address)
            return result
        o.hooks[address&~1]=callback
    def native(_,address):
        native_calls.append(address)
        return returns[address]
    cb=CALL(native)
    tasks=C.create_string_buffer(216)
    lib.syscon_tasks_poll.argtypes=[C.c_void_p,C.c_uint64,CALL,C.c_void_p]
    lib.syscon_tasks_submit.argtypes=[C.c_void_p,C.c_void_p,C.c_uint]
    rng=random.Random(0x7554)
    for epoch in [0,1,0xfffffff0,0x100000000,0x1fffffff0]:
        lib.syscon_tasks_init(tasks)
        o.call(0x7540)
        now[0]=epoch
        for step in range(250):
            if rng.randrange(3)==0:
                count=rng.randrange(0,15)
                actions=bytearray()
                for _ in range(count):
                    kind=rng.choice([0,0,1,1,2])
                    value=rng.choice(list(returns)) if kind==0 else rng.randrange(0,1000)
                    actions+=struct.pack('<B3sI',kind,rng.randbytes(3),value)
                o.put(0x20000900,actions or b'\0')
                expected=C.c_int32(o.call(0x7554,0x20000900,count)).value
                assert lib.syscon_tasks_submit(tasks,C.c_char_p(bytes(actions)),count)==expected
            else:
                now[0]+=rng.randrange(0,400)
                o.call(0x75d8)
                lib.syscon_tasks_poll(tasks,now[0],cb,None)
            assert tasks.raw==bytes(o.cpu.mem_read(0x20000534,216)),(epoch,step)
            assert native_calls==original_calls
            assert lib.syscon_tasks_active(tasks)==o.call(0x76d8)
