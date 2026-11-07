"""Original SysTick -> RGB -> PWM -> register pipeline, without subsystem hooks."""
import ctypes as C
import pytest
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from test_pwm import Pair as PwmPair, READ, WRITE
from test_rgb import Io as RgbIo, PWM_INIT, PWM_WRITE, REGISTER, NOTIFY

TIMER_CALL=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32,C.c_uint32)

@pytest.mark.parametrize('initialize_timer_first',[False,True])
def test_real_systick_rgb_pwm_pipeline_and_initialization_order(lib,initialize_timer_first):
    p=PwmPair(lib)
    o=p.original
    o.cpu.mem_map(0xe000e000,0x1000)
    o.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,o._mmio,begin=0xe000e000,end=0xe000efff)
    rgb=C.create_string_buffer(bytes(o.cpu.mem_read(0x200003a8,28)),28)
    timers=C.create_string_buffer(bytes(o.cpu.mem_read(0x20000610,112)),112)
    lib.syscon_timer_init.argtypes=[C.c_void_p,READ,WRITE,C.c_void_p]
    lib.syscon_timer_register.argtypes=[C.c_void_p,C.c_uint32,C.c_uint8,C.c_uint32,C.c_uint32]
    lib.syscon_timer_tick.argtypes=[C.c_void_p,TIMER_CALL,C.c_void_p]
    def timer_init(): lib.syscon_timer_init(timers,p.io.read,p.io.write,None)
    def register(_,period,once,callback,argument):
        return lib.syscon_timer_register(timers,period,once,callback,argument)
    io=RgbIo(None,
        PWM_INIT(lambda _,pin:lib.syscon_pwm_init(p.board,C.byref(p.io),pin)),
        PWM_WRITE(lambda _,pin,value:lib.syscon_pwm_write(p.board,C.byref(p.io),pin,value)),
        REGISTER(register),NOTIFY(lambda _:timer_init()),NOTIFY(lambda _:None))
    def dispatch(_,callback,argument):
        assert callback==0x5cad and argument==0
        lib.syscon_rgb_tick(rgb,C.byref(io))
    callback=TIMER_CALL(dispatch)
    def check():
        assert rgb.raw==bytes(o.cpu.mem_read(0x200003a8,28))
        assert timers.raw==bytes(o.cpu.mem_read(0x20000610,112))
        p.check()
    if initialize_timer_first:
        o.call(0x776c);timer_init();check()
    o.call(0x5b7c,0)
    lib.syscon_rgb_init(rgb,C.byref(io),0)
    check()
    for state,duration,count in [(5,0,600),(8,100,300),(3,0,100)]:
        o.call(0x5c68,state,duration)
        lib.syscon_rgb_set_state(rgb,C.byref(io),state,duration)
        check()
        for _ in range(count):
            o.call(0x76f8)
            lib.syscon_timer_tick(timers,callback,None)
            check()
