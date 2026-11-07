import random
import struct
import pytest
from unicorn import UcError
from unicorn.arm_const import UC_ARM_REG_R1,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
from arm_rebuild_oracle import ArmRebuildOracle
from build_arm_test_image import build
from rgb_oracle import RgbOracle
from sg560d_oracle import SG560DOracle,DEPENDENCIES,PAYLOADS
from timer_oracle import TimerOracle
from oracle import Oracle,REGS


def call_original_varargs(oracle,entry,*words):
    # Leave enough caller stack space for more than the base oracle's four
    # extra words; both caller SPs remain8-byte aligned per AAPCS.
    sp=0x20000fc0
    assert sp+max(0,len(words)-4)*4<=0x20001000
    oracle.cpu.reg_write(UC_ARM_REG_SP,sp)
    oracle.cpu.reg_write(UC_ARM_REG_LR,oracle.SENTINEL|1)
    for i,word in enumerate(words):
        if i<4:oracle.cpu.reg_write(REGS[i],word&0xffffffff)
        else:oracle.put(sp+4*(i-4),struct.pack('<I',word&0xffffffff))
    oracle.cpu.emu_start(entry|1,oracle.SENTINEL,count=500000)
    assert oracle.cpu.reg_read(UC_ARM_REG_PC)==oracle.SENTINEL
    return oracle.cpu.reg_read(REGS[0])


@pytest.fixture(scope='module')
def arm_elf(tmp_path_factory):
    return build(tmp_path_factory.mktemp('rebuilt-arm'))


def test_added_compiler_shift_helper_is_defined_at_boundaries(arm_elf):
    arm=ArmRebuildOracle(arm_elf);rng=random.Random(0x1152)
    for value in [0,1,0x8000000000000000,0xffffffffffffffff,*[rng.getrandbits(64) for _ in range(60)]]:
        for shift in [0,1,31,32,33,63,64,65,255,0xffffffff]:
            low=arm.call('__aeabi_llsr',value&0xffffffff,value>>32,shift)
            actual=low|(arm.cpu.reg_read(UC_ARM_REG_R1)<<32)
            assert actual==(value>>shift if shift<64 else 0)


class RgbPair:
    def __init__(self,elf,state=bytes(28),timer_result=0):
        self.original=RgbOracle(state,timer_result)
        self.arm=ArmRebuildOracle(elf)
        self.arm.put(self.original.STATE,state)
        self.events=[]
        def pwm_init(cpu):self.events.append(('pwm-init',cpu.arg(1)))
        def pwm_write(cpu):self.events.append(('pwm-write',cpu.arg(1),cpu.arg(2)))
        def register(cpu):
            self.events.append(('register',*(cpu.arg(i) for i in range(1,5))))
            return timer_result
        callbacks=[pwm_init,pwm_write,register,
            lambda _:self.events.append(('timer-init',)),lambda _:self.events.append(('timer-error',))]
        self.io=self.arm.allocate(struct.pack('<6I',0,*(self.arm.callback(fn) for fn in callbacks)))

    def compare(self):
        assert self.arm.read(self.original.STATE,28)==self.original.state()
        assert self.events==self.original.events

    def call(self,symbol,entry,*args,returns=True):
        expected=self.original.call(entry,*args)
        actual=self.arm.call('syscon_rgb_'+symbol,self.original.STATE,self.io,*args)
        if returns:assert actual==expected
        self.compare()

    def tick(self):self.call('tick',0x5cac,returns=False)


def test_arm_rgb_scaling_float_conversion_edges_and_all_channels(arm_elf):
    rng=random.Random(0xa5b20)
    pair=RgbPair(arm_elf)
    bits=[0,0x80000000,1,0x007fffff,0x00800000,0x7f800000,0xff800000,
        0x7fc12345,0xffc12345,0x7f800001,0xff800001,0x4effffff,0x4f000000,0x4f800000]
    bits += [rng.getrandbits(32) for _ in range(100)]
    bits += [struct.unpack('<I',struct.pack('<f',float(level)))[0] for level in range(101)]
    for raw in bits:
        for polarity in (0,1):
            state=bytearray(28);struct.pack_into('<I',state,8,raw);state[16]=polarity
            pair.original.put(pair.original.STATE,state);pair.arm.put(pair.original.STATE,state)
            for channel in (0,1,127,254,255,256,0xffffffff):
                expected=pair.original.call(0x5b20,channel)
                actual=pair.arm.call('syscon_rgb_scale',pair.original.STATE,channel)
                assert actual==expected,(hex(raw),polarity,channel,actual,expected)


@pytest.mark.parametrize('state',range(10))
def test_arm_rgb_presets_full_cycles_and_temporary_state_restore(arm_elf,state):
    pair=RgbPair(arm_elf,bytes(range(28)),timer_result=-1)
    pair.call('init',0x5b7c,state&1)
    pair.call('set_state',0x5c68,state,0)
    for _ in range(240):pair.tick()
    pair.call('set_state',0x5c68,(state+1)%10,40)
    for _ in range(5):pair.tick()


def test_arm_rgb_float_tick_corrupt_and_boundary_representations(arm_elf):
    rng=random.Random(0xa5cac)
    pair=RgbPair(arm_elf)
    patterns=[0,0x80000000,1,0x007fffff,0x00800000,0x7f800000,0xff800000,
              0x7fc12345,0xffc12345,0x7f800001,0xff800001]
    patterns += [rng.getrandbits(32) for _ in range(80)]
    for raw in patterns:
        for increasing in (0,1):
            state=bytearray(28);state[:5]=bytes([1,23,100,255,100])
            state[12]=increasing;state[16]=1;struct.pack_into('<I',state,8,raw)
            pair.original.put(pair.original.STATE,state);pair.arm.put(pair.original.STATE,state)
            pair.tick()


class SGPair:
    def __init__(self,elf,initial=None,responses=None):
        self.responses=responses or {};self.events=[]
        def respond(fn,args):return self.responses.get((fn,args),self.responses.get(fn,0))&0xffffffffffffffff
        self.respond=respond
        self.original=SG560DOracle(respond);self.arm=ArmRebuildOracle(elf)
        if initial is None:initial=bytes(self.original.cpu.mem_read(0x20000000,4096))
        self.original.put(0x20000000,initial);self.arm.put(0x20000000,initial)
        def dependency(cpu):
            fn=cpu.arg(1)
            if fn==0x7554:
                args=(cpu.arg(3),);data=cpu.read(cpu.arg(6),cpu.arg(7))
            elif fn in PAYLOADS:
                args=(cpu.arg(2),);data=cpu.read(cpu.arg(6),cpu.arg(7))
            else:args=tuple(cpu.arg(i+2) for i in range(DEPENDENCIES[fn]));data=b''
            self.events.append((fn,args,data));return respond(fn,args)
        self.env=self.arm.allocate(struct.pack('<II',self.arm.callback(dependency),0))

    def call(self,entry,a=0,b=0,returns=True):
        self.original.hooks.pop(entry,None)
        if entry==0x6282:self.original.hooks.pop(0x5e30,None)
        expected=self.original.call(entry,a,b)
        actual=self.arm.call('sg560d_execute',0x20000000,self.env,entry,a,b)
        if returns:assert actual==expected,(hex(entry),a,b,actual,expected)
        assert self.arm.state()[:0x800]==bytes(self.original.cpu.mem_read(0x20000000,0x800)),hex(entry)
        assert self.events==self.original.events,(hex(entry),self.events,self.original.events)


def test_arm_sg560d_64_bit_wake_and_retry_policy(arm_elf):
    for now in (0,1,0xffffffff,0x100000001,0xffffffffffffffff):
        pair=SGPair(arm_elf,responses={0x77b4:now})
        for seconds in (0,1,1000,0xffffffff):
            pair.call(0x65f0,seconds,returns=False);pair.call(0x6650)
    pair=SGPair(arm_elf)
    for temperature in (499,500):
        pair.responses[0x7d54]=temperature
        for reason in range(10):
            for count in (0,1,2,3,32,0xffffffff):pair.call(0x62ec,reason,count)


def test_arm_sg560d_stack_payloads_and_power_decisions(arm_elf):
    for entry,a in [(0x6428,0),(0x64a0,0),(0x6520,0),(0x6520,1),(0x65d0,0),(0x65e4,0)]:
        for task_result in (-1,0,1):
            pair=SGPair(arm_elf,responses={0x7554:task_result});pair.call(entry,a)
    rng=random.Random(0xa5f30)
    for _ in range(100):
        responses={0x5274:rng.randrange(3),0x4ca8:rng.randrange(3),0x3194:rng.randrange(2),
            0x4d9c:rng.randrange(3),0x4ee0:rng.choice([0,-1]),0x4e34:rng.choice([0,-1]),
            0x77b4:rng.choice([0,0xffffffff,0xffffffffffffffff])}
        for pin in (13,14,15,16):responses[(0x4c50,(pin,))]=rng.choice([1699,1700,1999,2000,4499,4500,4501])
        SGPair(arm_elf,responses=responses).call(0x5f30)


def test_arm_sg560d_poll_state_and_external_trace(arm_elf):
    rng=random.Random(0xa6a68)
    for _ in range(180):
        initial=bytearray(4096)
        initial[0x4f1]=rng.choice([0,2]);initial[0x4f2]=rng.randrange(4)
        initial[0x450]=rng.randrange(1,6)
        for offset in (0x3cf,0x4f8,0x508,0x509,0x50a,0x4f0):initial[offset]=rng.randrange(2)
        initial[0x528]=rng.randrange(7)
        initial[0x3cc:0x3cf]=bytes(rng.randrange(2) for _ in range(3))
        initial[0x4f9:0x4fc]=rng.randbytes(3)
        now=rng.choice([0,1,10000,120000,0xffffffff,0x100000000,0xffffffffffffffff])
        for offset in (0x458,0x4e0,0x4e8,0x500,0x510,0x518,0x520):
            struct.pack_into('<Q',initial,offset,rng.choice([0,1,now,(now-1)&0xffffffffffffffff,(now+1)&0xffffffffffffffff]))
        for offset in (0x454,0x52c,0x530):struct.pack_into('<I',initial,offset,rng.choice([0,1,now&0xffffffff]))
        struct.pack_into('<I',initial,0x4f4,rng.randrange(7))
        responses={0x77b4:now,0x7d54:rng.choice([499,500]),0x76d8:rng.randrange(2),
            0x3150:rng.randrange(2),0x3114:rng.randrange(2),0x517c:rng.randrange(2),
            0x562c:rng.randrange(7),0x567c:rng.randrange(7),0x5670:rng.randrange(2),
            0x5638:rng.choice([0,4999,5000,30000,120000,0x100000000]),
            0x55c4:rng.choice([2499,2500]),0x5dbc:rng.randrange(8),0x7554:rng.choice([-1,0,1])}
        for pin in (12,13,14,15,16):responses[(0x4c50,(pin,))]=rng.choice([0,1699,1700,4499,4500])
        for pin in (18,19,20):responses[(0x80f8,(pin,))]=rng.randrange(2)
        SGPair(arm_elf,initial,responses).call(0x6a68,returns=False)


def test_arm_timer_register_fifth_argument_and_64_bit_clock(arm_elf):
    original=TimerOracle();arm=ArmRebuildOracle(arm_elf)
    initial=bytearray(112);struct.pack_into('<Q',initial,104,0xffffffffffffffff)
    original.put(original.STATE,initial);arm.put(original.STATE,initial)
    expected=original.call(0x781c,10,1,0x10021,0xdeadbeef)
    assert arm.call('syscon_timer_register',original.STATE,10,1,0x10021,0xdeadbeef)==expected
    assert arm.read(original.STATE,112)==original.state()
    callback=arm.callback(lambda cpu:None)
    original.call(0x76f8)
    arm.call('syscon_timer_tick',original.STATE,callback,0)
    assert arm.read(original.STATE,112)==original.state()
    lo=original.call(0x77b4);hi=original.cpu.reg_read(UC_ARM_REG_R1)
    assert arm.call('syscon_timer_now',original.STATE)==lo
    assert arm.cpu.reg_read(UC_ARM_REG_R1)==hi


def test_arm_loader_rejects_execution_of_original_firmware(arm_elf):
    arm=ArmRebuildOracle(arm_elf)
    with pytest.raises(UcError):arm.call(0x5b20,1)


def test_arm_variadic_snprintf_register_stack_and_64_bit_alignment(arm_elf):
    reference=Oracle();arm=ArmRebuildOracle(arm_elf)
    rng=random.Random(0xa92f4)
    fmt,output,string=0x20000400,0x20000900,0x20000780
    for cpu in (reference,arm):cpu.put(string,b'ARM32 string\0')
    formats=[b'%u/%lld/%u',b'%lld/%u/%llu',b'%ju/%zu/%tu',b'%cafter',b'%s/%ls/%hhs',
        b'%p/%p/%p',b'',b'%%',b'x'*127,b'x'*128,b'%03d %.2f %f %e %-s']
    formats += [b'%'+length+spec+b'/tail%u' for length in (b'',b'h',b'hh',b'l',b'll',b'j',b'z',b't')
                for spec in (b'd',b'i',b'u',b'o',b'x',b'X')]
    for text in formats:
        words=[string]*12 if b's' in text else [rng.getrandbits(32) for _ in range(12)]
        for cap in (0,1,7,31,128):
            for destination in (0,output):
                initial=b'\xa5'*256
                for cpu in (reference,arm):
                    cpu.put(fmt,text+b'\0');cpu.put(output,initial)
                expected=call_original_varargs(reference,0x92f4,destination,cap,fmt,*words)
                actual=arm.call('syscon_target_snprintf',destination,cap,fmt,*words)
                assert actual==expected,(text,cap,actual,expected)
                assert arm.read(output,256)==bytes(reference.cpu.mem_read(output,256)),(text,cap)


class ArmLogPair:
    def __init__(self,elf):
        self.original=Oracle();self.arm=ArmRebuildOracle(elf)
        self.original_events=[];self.arm_events=[]
        self.now=0x100000000+12345
        self.original_colors=[];self.arm_colors=[]
        def original_now(cpu):
            self.original_events.append(('clock',self.now));cpu.cpu.reg_write(UC_ARM_REG_R1,self.now>>32)
            return self.now&0xffffffff
        def original_color(cpu):
            value=self.original_colors.pop(0);self.original_events.append(('color',value));return value
        def original_write(cpu):
            self.original_events.append(('write',0,bytes(cpu.cpu.mem_read(cpu.arg(0),cpu.arg(1)))))
        def original_uart(cpu):
            self.original_events.append(('write',cpu.arg(0),bytes(cpu.cpu.mem_read(cpu.arg(1),cpu.arg(2)))))
        self.original.hooks.update({0x77b4:original_now,0x312c:original_color,0x3af4:original_write,0x8c8c:original_uart})
        def arm_now(cpu):self.arm_events.append(('clock',self.now));return self.now
        def arm_color(cpu):
            value=self.arm_colors.pop(0);self.arm_events.append(('color',value));return value
        def arm_write(cpu):self.arm_events.append(('write',cpu.arg(0),cpu.read(cpu.arg(1),cpu.arg(2))))
        for symbol,fn in [('syscon_target_now',arm_now),('syscon_target_color',arm_color),('syscon_target_uart_write',arm_write)]:
            self.arm.hooks[self.arm.symbols[symbol]&~1]=fn

    def run(self,entry,text,words,*,enabled=1,level=3,colors=(1,1)):
        self.original_events.clear();self.arm_events.clear()
        self.original_colors=list(colors);self.arm_colors=list(colors)
        fmt,tag=0x20000400,0x20000700
        for cpu in (self.original,self.arm):
            cpu.put(fmt,text+b'\0');cpu.put(tag,b'TEST\0');cpu.put(0x2000080c,bytes([enabled]))
        if entry==0x8f88:
            original_args=(level,tag,fmt,*words);symbol='syscon_target_logger'
        else:
            original_args=(fmt,*words)
            symbol='syscon_target_mfg_logger' if entry==0x8fa0 else 'syscon_target_sg560d_printf'
        call_original_varargs(self.original,entry,*original_args)
        self.arm.call(symbol,*original_args) # Original logger/SG wrappers return void.
        assert self.arm_events==self.original_events,(hex(entry),text,enabled,level,colors,self.arm_events,self.original_events)


def test_arm_variadic_logger_wrappers_and_sg_uart_truncation(arm_elf):
    pair=ArmLogPair(arm_elf)
    words=[0,0xffffffff,0x12345678,0x7fffffff,0x89abcdef,1,2,3]
    formats=[b'',b'a',b'%c%u %lld %p',b'%lld/%u/%llu',b'X'*31,b'X'*32,b'X'*127,b'X'*128,b'X'*255,b'X'*256,b'X'*300]
    for entry in (0x8f88,0x8fa0,0x5edc):
        for text in formats:
            for enabled in (0,1):
                for colors in ((0,0),(1,1),(0,1),(1,0)):
                    pair.run(entry,text,words,enabled=enabled,level=3,colors=colors)
    for level in (0,1,2,3,4,5,0xffffffff):pair.run(0x8f88,b'level %u',words,level=level)


def test_arm_unbound_target_io_fails_closed(arm_elf):
    arm=ArmRebuildOracle(arm_elf)
    with pytest.raises(UcError):arm.call('syscon_target_now')
