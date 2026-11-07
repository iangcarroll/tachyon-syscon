"""Original power/IO/I2C code versus reconstructed modules at MMIO boundary."""
import collections
import ctypes as C
import random
import pytest
from power_io_environment import PowerIoPeripheral,PowerIoOracle,NativePowerIo,explicit_mmio_state
from i2c_oracle import BASE
from adc_oracle import ADC


class Pair:
    def __init__(self,lib,registers=None,initialized=1,stuck_native=0):
        if registers is None:registers=bytes(8)
        self.original=PowerIoPeripheral(registers,explicit_mmio_state())
        self.native_model=PowerIoPeripheral(registers,explicit_mmio_state(),stuck_low=stuck_native)
        self.oracle=PowerIoOracle(self.original)
        self.oracle.put(0x200002d0,bytes([initialized]))
        self.native=NativePowerIo(lib,self.native_model,bytes(self.oracle.cpu.mem_read(0x20000000,4096)))
        config=bytes([0,0,7,0,8,7,12])
        self.oracle.put(self.oracle.DATA,config)
        assert self.oracle.invoke(0x7c54,13,self.oracle.DATA)==self.native.adc_init(13,config)==0

    def check(self):
        assert self.native_model.events==self.original.events,'MMIO/wire/dependency trace mismatch'
        assert self.native.ram.raw[:0x800]==bytes(self.oracle.cpu.mem_read(0x20000000,0x800)),'global RAM mismatch'
        assert self.native_model.expander==self.original.expander,'expander register mismatch'
        assert self.native_model.pointer==self.original.pointer,'expander pointer mismatch'
        assert self.native_model.mmio==self.original.mmio,'MMIO state mismatch'
        assert self.native_model.tx==self.original.tx
        assert self.native_model.rx==self.original.rx
        assert self.native_model.active==self.original.active
        assert self.native_model.pending_irqs==self.original.pending_irqs
        assert self.native_model.now==self.original.now
        assert self.native_model.failures==self.original.failures

    def io(self,name,entry,*args,compare_result=True):
        expected=self.oracle.invoke(entry,*args)
        actual=self.native.io_call(name,*args)
        if expected>=0x80000000:expected-=0x100000000
        if compare_result or expected==-2:assert actual==expected,(name,actual,expected)
        self.check()
        return actual

    def configure(self,pin,data):
        self.oracle.put(self.oracle.DATA,data)
        expected=self.oracle.invoke(0x386c,pin,self.oracle.DATA)
        actual=self.native.io_call('syscon_io_configure',pin,C.c_char_p(data))
        assert actual==expected
        self.check()

    def read(self,pin):
        self.oracle.put(self.oracle.DATA,b'\xa5')
        expected=self.oracle.invoke(0x39e8,pin,self.oracle.DATA)
        value=C.c_uint8(0xa5)
        actual=self.native.io_call('syscon_io_read',pin,C.byref(value))
        assert actual==expected
        assert value.value==self.oracle.cpu.mem_read(self.oracle.DATA,1)[0]
        self.check()

    def power(self,entry,a=0):
        expected=self.oracle.invoke(entry,a)
        actual=self.native.power(entry,a)
        # Several setters are void in the original; compare only meaningful returns.
        if entry in [0x4c50,0x4ca8,0x4d00,0x4d9c,0x4d58,0x4df4,0x4ec4,0x5274] or expected==-2:
            assert actual==expected,(hex(entry),actual,expected)
        self.check()
        return actual

    def failures(self,plan):
        self.original.failures.extend(plan);self.native_model.failures.extend(plan)


def test_full_io_initialization_through_real_i2c_and_power_routing(lib):
    p=Pair(lib,bytes([0xa5,0x5a,0x91,0x72,0x32,0x44,0x55,0x66]),initialized=0)
    p.io('syscon_io_init',0x3808,1)
    for pin in range(16):p.configure(pin,b'\1\0\1')
    rng=random.Random(0x5048)
    for iteration in range(80):
        entry=rng.choice([0x4e34,0x5048,0x4ee0])
        p.power(entry,rng.randrange(3))
        for getter in [0x4ca8,0x4d00,0x4d9c]:p.power(getter)
    assert any(e[0]=='wire-write' for e in p.original.events)
    assert any(e[0]=='wire-read' for e in p.original.events)
    # Regression guard: the oracle must execute, not hook, each module boundary.
    for entry in [0x4e34,0x3620,0x364e,0x3940,0x39e8,0x844c,0x860c,0x7c54,0x7f24,0x7e7c]:
        assert entry in p.oracle.executed
        assert entry not in p.oracle.hooks


def test_all_io_pins_directions_and_external_input_changes_over_mmio(lib):
    p=Pair(lib,bytes([0x96,0x69,0x53,0xac,0x12,0x34,0xff,0xff]))
    rng=random.Random(0x9535)
    for pin in range(16):
        for output in [0,1]:
            p.configure(pin,bytes([output,rng.randrange(2),1]))
            p.read(pin)
            p.io('syscon_io_write',0x3940,pin,rng.randrange(2))
            p.read(pin)
    for value in [0,0x55,0xaa,0xff]:
        p.original.expander[0]=p.native_model.expander[0]=value
        for pin in range(8):
            p.configure(pin,b'\0\0\0');p.read(pin)


def test_power_measurements_and_battery_detection_execute_actual_adc_hal(lib):
    for sample in [0,1,910,911,2730,2731,4095,65535]:
        p=Pair(lib)
        for model in [p.original,p.native_model]:model.mmio[ADC+0x556280]=sample
        for pin in [12,13,14,15,16,23]:p.power(0x4c50,pin)
        p.power(0x5274)
        assert 0x7f24 in p.oracle.executed and 0x7f24 not in p.oracle.hooks


@pytest.mark.parametrize('nacks',[0,1,2,3,4])
def test_write_nack_retries_use_actual_irq_and_leave_failed_frames_unapplied(lib,nacks):
    p=Pair(lib)
    p.failures(['nack']*nacks)
    result=p.io('syscon_io_write8',0x374c,2,0x5a,compare_result=False)
    assert (result==-2)==(nacks==4)
    if nacks:
        assert 0x8798 in p.oracle.executed
        assert 0x8798 not in p.oracle.hooks
        assert any(event[0]=='irq-enter' for event in p.original.events)


def test_read_nack_stays_sticky_across_read_retry_attempts(lib):
    p=Pair(lib)
    p.failures([None,'nack']) # Pointer write succeeds; first read NACKs.
    p.oracle.put(p.oracle.DATA,b'\xa5')
    expected=p.oracle.invoke(0x36bc,2,p.oracle.DATA)
    value=C.c_uint8(0xa5)
    actual=p.native.io_call('syscon_io_read8',2,C.byref(value))
    assert expected==actual==-2
    assert value.value==p.oracle.cpu.mem_read(p.oracle.DATA,1)[0]
    p.check()
    assert p.native.ram.raw[0x760]==1


def test_idle_timeout_then_successful_retry_crosses_controller_cleanup(lib):
    p=Pair(lib)
    for model in [p.original,p.native_model]:model.read_scripts[BASE+0x1218]=collections.deque([0]*10000)
    p.io('syscon_io_write16',0x3668,2,0x1234,compare_result=False)
    assert 0x82b4 in p.oracle.executed
    assert any(event==('cycles',32) for event in p.original.events)


def test_power_mode_invalid_selector_assertion_matches_after_real_bus_reads(lib):
    # Battery selector outputs8 and9 bothhigh is an invalid physical selector state.
    p=Pair(lib,bytes([0,0,0,3,0,0,0,0]))
    assert p.power(0x4ca8)==-2


def test_terminal_i2c_assertion_stops_power_path_immediately(lib):
    p=Pair(lib)
    p.failures(['nack']*4)
    assert p.power(0x4e34,1)==-2


@pytest.mark.parametrize('entry',[0x4e34,0x5048,0x4ee0])
def test_power_routing_recovers_transient_nacks_through_actual_irq(lib,entry):
    p=Pair(lib)
    p.failures(['nack']*3)
    p.power(entry,1)
    assert any(event[0]=='irq-enter' for event in p.original.events)
    assert not any(event[0]=='assert' for event in p.original.events)


def test_i2c_hal_assertion_is_not_retried_as_controller_failure(lib):
    p=Pair(lib)
    p.oracle.put(0x20000761,b'\1')
    C.memmove(C.addressof(p.native.ram)+0x761,b'\1',1)
    assert p.power(0x4e34,1)==-2


def test_negative_control_rejects_native_only_stuck_power_selector(lib):
    p=Pair(lib,stuck_native=1<<10) # GPIO35, the SG560D VBUS first selector.
    with pytest.raises(AssertionError):p.power(0x5048,1)
    assert any(event[0]=='assert' for event in p.native_model.events)
    assert not any(event[0]=='assert' for event in p.original.events)
    assert p.native_model.expander!=p.original.expander
