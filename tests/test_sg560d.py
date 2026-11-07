import ctypes as C
import random
import struct
import pytest
from sg560d_oracle import SG560DOracle,DEPENDENCIES,PAYLOADS

DEPENDENCY=C.CFUNCTYPE(C.c_uint64,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,
                       C.c_uint32,C.c_uint32,C.c_void_p,C.c_size_t)

class Environment(C.Structure):
    _fields_=[('call',DEPENDENCY),('ctx',C.c_void_p)]


@pytest.fixture
def sg_lib(lib):
    lib.sg560d_execute.argtypes=[C.c_void_p,C.POINTER(Environment),C.c_uint32,C.c_uint32,C.c_uint32]
    lib.sg560d_execute.restype=C.c_uint64
    return lib


def run_comparison(lib,entry,a=0,b=0,*,initial=None,responses=None,check_return=True):
    responses=responses or {}
    def response(f,args):
        value=responses.get((f,args),responses.get(f,0))
        return value&0xffffffffffffffff
    o=SG560DOracle(response)
    # Execute the requested entry even when callers normally treat it as an
    # explicit external dependency in a higher-layer test.
    o.hooks.pop(entry,None)
    if entry==0x6282:o.hooks.pop(0x5e30,None)
    if initial is not None:o.put(0x20000000,initial)
    state=C.create_string_buffer(bytes(o.cpu.mem_read(0x20000000,4096)),4096)
    events=[]
    def callback(_,f,a0,a1,a2,a3,payload,length):
        if f==0x7554:
            args=(a1,);data=C.string_at(payload,length)
        elif f in PAYLOADS:
            args=(a0,);data=C.string_at(payload,length)
        else:
            args=(a0,a1,a2,a3)[:DEPENDENCIES[f]];data=b''
        events.append((f,args,data))
        return response(f,args)
    cb=DEPENDENCY(callback);env=Environment(cb,None)
    expected=o.call(entry,a,b)
    got=lib.sg560d_execute(state,C.byref(env),entry,a,b)
    if check_return:assert got&0xffffffff==expected,(hex(entry),a,b,got,expected)
    assert state.raw[:0x800]==bytes(o.cpu.mem_read(0x20000000,0x800)),(hex(entry),a,b)
    assert events==o.events,(hex(entry),a,b,events,o.events)
    return state.raw,events


def test_sg560d_retry_policy_thermal_exponential_boundaries(sg_lib):
    for temperature in (-100,499,500,1100):
        for reason in range(10):
            for attempts in (0,1,2,3,10,0xffffffff):
                run_comparison(sg_lib,0x62ec,reason,attempts,responses={0x7d54:temperature})


def test_sg560d_mode_and_callback_helpers(sg_lib):
    for mode in list(range(8))+[255,256,257,0xffffffff]:
        run_comparison(sg_lib,0x66a0,mode)
        run_comparison(sg_lib,0x66bc,mode)
    for entry in [0x61b8,0x61d0,0x61f0,0x6210,0x6230,0x6238,0x6240,0x7488,0x74a8,0x74c8]:
        run_comparison(sg_lib,entry)
    for a,b in [(0,0),(8,1),(39,0),(255,0xffffffff)]:run_comparison(sg_lib,0x7468,a,b)
    for entry in (0x6a28,0x6a48):run_comparison(sg_lib,entry,check_return=False)


def test_sg560d_wake_schedule_wrap_and_remaining(sg_lib):
    rng=random.Random(0x65f0)
    for now in (0,1,0xfffffff0,0xffffffffffffffff):
        for seconds in (0,1,0xffffffff):
            initial=bytearray(4096);initial[0x458:0x460]=rng.randbytes(8)
            run_comparison(sg_lib,0x65f0,seconds,initial=initial,responses={0x77b4:now},check_return=False)
        for deadline in (0,1,now,(now+999)&0xffffffffffffffff,(now+2001)&0xffffffffffffffff,0xffffffffffffffff):
            initial=bytearray(4096);struct.pack_into('<Q',initial,0x458,deadline)
            run_comparison(sg_lib,0x6650,initial=initial,responses={0x77b4:now})


def test_sg560d_retry_state_preserves_sticky_invalid_reason(sg_lib):
    rng=random.Random(0x6384)
    for reason in range(9):
        for active in (0,1,255):
            for old_reason in (reason,7):
                initial=bytearray(rng.randbytes(0x800))+bytearray(0x800)
                initial[0x508]=active;initial[0x528]=old_reason
                struct.pack_into('<I',initial,0x4f4,2)
                run_comparison(sg_lib,0x6384,reason,initial=initial,
                    responses={0x77b4:0xfffffffffffffff0,0x7d54:500},check_return=False)


def test_sg560d_boot_modes_task_failure_and_busy_gate(sg_lib):
    for entry,a in [(0x6428,0),(0x64a0,0),(0x6520,0),(0x6520,1),(0x65d0,0),(0x65da,0),(0x65e4,0)]:
        for busy in (0,1,2,255):
            for task_result in (-1,0,1):
                initial=bytearray(4096);initial[0x4f1]=busy
                initial[0x508]=1;initial[0x528]=5
                run_comparison(sg_lib,entry,a,initial=initial,responses={0x7554:task_result})


def test_sg560d_power_off_dependency_failures_and_busy_gate(sg_lib):
    rng=random.Random(0x6720)
    for force in (0,1):
        for tasks in (0,1,255):
            for voltage in (0,1699,1700,4000):
                for keep_on in (0,1):
                    initial=bytearray(rng.randbytes(0x800))+bytearray(0x800)
                    run_comparison(sg_lib,0x6720,force,initial=initial,responses={
                        0x76d8:tasks,0x4c50:voltage,0x3150:keep_on,0x77b4:0xfffffffffffffff0,
                        0x5048:-1,0x4e34:-1,0x4fd0:-1,0x4ee0:-1,0x4ed4:-1})


def test_sg560d_boot_preparation_and_initial_power_detection(sg_lib):
    for entry in (0x6838,0x68a4,0x68fc):
        for success in (0,1):
            for target in (3,5):
                initial=bytearray(4096);initial[0x3c4]=target
                run_comparison(sg_lib,entry,initial=initial,responses={0x5f30:success,0x77b4:0x100000001})
    for mode in range(7):
        for voltage in (0,1699,1700):
            for keep in (0,1):
                run_comparison(sg_lib,0x6948,mode,responses={0x4c50:voltage,0x3150:keep,0x77b4:0x100000001,0x4fd0:-1})
    for power in (0,1,2,255):
        initial=bytearray(4096);initial[0x4f1]=power
        run_comparison(sg_lib,0x6690,initial=initial)


def test_sg560d_poll_differential_branch_combinations(sg_lib):
    rng=random.Random(0x6a68)
    for iteration in range(1200):
        initial=bytearray(4096)
        current=rng.choice([0,2]);target=rng.randrange(4)
        initial[0x4f1]=current;initial[0x4f2]=target
        initial[0x450]=rng.randrange(1,6)
        initial[0x3cf]=rng.randrange(2)
        initial[0x4f8]=rng.randrange(2)
        initial[0x508]=rng.randrange(2);initial[0x528]=rng.randrange(7)
        initial[0x509]=rng.randrange(2);initial[0x50a]=rng.randrange(2)
        initial[0x4f0]=rng.randrange(2)
        initial[0x3cc:0x3cf]=bytes(rng.randrange(2) for _ in range(3))
        initial[0x4f9:0x4fc]=rng.randbytes(3)
        now=rng.choice([0,1,10000,119999,120000,0xffffffff,0x100000000,0xffffffffffffffff])
        for offset in [0x458,0x4e0,0x4e8,0x500,0x510,0x518,0x520]:
            struct.pack_into('<Q',initial,offset,rng.choice([0,1,now,(now-1)&0xffffffffffffffff,(now+1)&0xffffffffffffffff]))
        for offset in [0x454,0x52c,0x530]:struct.pack_into('<I',initial,offset,rng.choice([0,1,now&0xffffffff]))
        struct.pack_into('<I',initial,0x4f4,rng.randrange(7))
        responses={0x77b4:now,0x7d54:rng.choice([499,500]),0x76d8:rng.randrange(2),
            0x3150:rng.randrange(2),0x3114:rng.randrange(2),0x517c:rng.randrange(2),
            0x562c:rng.randrange(7),0x567c:rng.randrange(7),0x5670:rng.randrange(2),
            0x5638:rng.choice([0,4999,5000,29999,30000,120000,0x100000000]),
            0x55c4:rng.choice([2499,2500]),0x5dbc:rng.randrange(8),0x7554:rng.choice([-1,0,1])}
        for pin in (12,13,14,15,16):responses[(0x4c50,(pin,))]=rng.choice([0,1699,1700,4499,4500])
        for pin in (18,19,20):responses[(0x80f8,(pin,))]=rng.randrange(2)
        try:run_comparison(sg_lib,0x6a68,initial=initial,responses=responses,check_return=False)
        except AssertionError as e:raise AssertionError(f'poll scenario {iteration}: {e}') from e


def test_sg560d_poll_rare_recovery_and_debounce_paths(sg_lib):
    scenarios=[]
    def scenario():
        state=bytearray(4096)
        state[0x50a]=1
        responses={0x77b4:10000,0x3114:1,0x7d54:499}
        scenarios.append((state,responses))
        return state,responses
    state,r=scenario()  # FCT reboot within its allowed window.
    state[0x450]=5;state[0x4f2]=1;state[0x3cf]=1
    struct.pack_into('<I',state,0x454,1);r[(0x4c50,(15,))]=1700
    for reason in (1,2):  # Reboot confirmation times out for distinct reasons.
        state,r=scenario();state[0x4f2]=state[0x3cf]=1
        struct.pack_into('<Q',state,0x518,9999);r[0x567c]=reason
    state,r=scenario()  # Sudden power loss with VPH below the brownout floor.
    state[0x4f1]=state[0x4f2]=2;r[0x55c4]=2499;r[0x562c]=0
    for clock in (10000,0x200000000):  # RGB green falls after longer than150ms.
        state,r=scenario();state[0x3cd]=1;state[0x4fa]=0
        struct.pack_into('<I',state,0x52c,1);r[0x77b4]=clock
    for usb,header in ((4500,0),(0,4500)):
        state,r=scenario();state[0x508]=1;state[0x528]=3
        r[(0x4c50,(16,))]=usb;r[(0x4c50,(13,))]=header
    state,r=scenario()  # Last shutdown reason owns the USB boot decision.
    r[0x567c]=2;r[(0x4c50,(16,))]=4500
    state,r=scenario()  # USB debounce has started but has not elapsed.
    state[0x4f0]=state[0x509]=1;r[(0x4c50,(16,))]=4500
    struct.pack_into('<Q',state,0x520,9000)
    for state,r in scenarios:
        run_comparison(sg_lib,0x6a68,initial=state,responses=r,check_return=False)


def test_sg560d_poll_multistep_usb_restore_and_rgb_debounce(sg_lib):
    state=bytearray(4096);state[0x50a]=1
    responses={0x3114:1,0x7d54:499,(0x4c50,(16,)):4500}
    for time in (100,1000,5099,5100):
        responses[0x77b4]=time
        state,events=run_comparison(sg_lib,0x6a68,initial=state,responses=responses,check_return=False)
        submitted=any(event[0]==0x7554 for event in events)
        assert submitted==(time==5100)
    # Keep the modem powered and feed three highs, then eight lows. The LED
    # algorithm uses three recent high samples but requires the whole8-bit
    # history to become zero before reporting low.
    state=bytearray(4096);state[0x4f1]=state[0x4f2]=2;state[0x50a]=1
    responses={0x3114:0,(0x4c50,(15,)):1700,(0x80f8,(19,)):1}
    for frame in range(1,4):
        responses[0x77b4]=frame*100
        state,_=run_comparison(sg_lib,0x6a68,initial=state,responses=responses,check_return=False)
        assert bool(state[0x3cd])==(frame==3)
    responses[(0x80f8,(19,))]=0
    for frame in range(1,9):
        responses[0x77b4]=300+frame*100
        state,_=run_comparison(sg_lib,0x6a68,initial=state,responses=responses,check_return=False)
        assert bool(state[0x3cd])==(frame<8)


def test_sg560d_uart_and_pin_configuration(sg_lib):
    rng=random.Random(0x6282)
    for entry in (0x5e30,0x614c,0x6248,0x6282):
        for enabled in (0,1,255):
            for result in (0,1,0xffffffff):
                initial=bytearray(4096);initial[0xed]=enabled
                initial[0x3d0:0x450]=rng.randbytes(128)
                initial[0x244]=rng.randrange(25);initial[0x247]=rng.randrange(25)
                run_comparison(sg_lib,entry,initial=initial,responses={0x8b50:result,0x8954:result},check_return=False)


def test_sg560d_power_check_supply_selection_and_failure_paths(sg_lib):
    rng=random.Random(0x5f30)
    for iteration in range(500):
        responses={0x5274:rng.randrange(3),0x4ca8:rng.randrange(3),0x3194:rng.randrange(2),
                   0x4d9c:rng.randrange(3),0x4ee0:rng.choice([0,-1]),0x4e34:rng.choice([0,-1]),
                   0x77b4:rng.choice([0,0xffffffff,0xffffffffffffffff])}
        for pin in (13,14,15,16):responses[(0x4c50,(pin,))]=rng.choice([1699,1700,1999,2000,4499,4500,4501])
        run_comparison(sg_lib,0x5f30,responses=responses)
