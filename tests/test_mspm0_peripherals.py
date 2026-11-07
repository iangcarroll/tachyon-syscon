"""Behavioral register tests using explicit external signals and fault controls."""
import pytest
from mspm0.core import MCU,ModelError,UnsupportedRegister
from mspm0.peripherals import MissingInput
from test_mspm0_emulator import fixture_image

@pytest.fixture
def m():return MCU(fixture_image())

def uart(m,port=0,fifo=True,threshold=2):
    base=m.device.BASES['UART'+str(port)]
    m.write_register(base+0x800,0x26000001)
    m.write_register(base+0x1100,0x19|(0x20000 if fifo else 0))
    m.write_register(base+0x110c,threshold<<4)
    m.write_register(base+0x1028,(1<<10)|(1<<4))
    return base

def test_uart_threshold_overrun_fifo_and_pending_are_separate(m):
    b=uart(m,threshold=3);d=m.device
    d.inject_uart(0,b'ab');assert not m.irq_lines&(1<<15)
    d.inject_uart(0,b'c');assert m.irq_lines&(1<<15)
    assert m.read_register(b+0x1124)==ord('a')
    assert not m.irq_lines&(1<<15) and 31 in m.pending
    d.inject_uart(0,b'def');assert bytes(d.rx[0])==b'bcde'
    assert m.read_register(b+0x1030)&(1<<4)
    assert not m.read_register(b+0x1030)&(1<<11)
    assert m.read_register(b+0x1020)==5
    assert m.read_register(b+0x1020)==11
    assert m.read_register(b+0x1020)==0
    assert bytes(m.read_register(b+0x1124) for _ in range(4))==b'bcde'
    with pytest.raises(MissingInput):m.read_register(b+0x1124)

def test_uart_character_mode_disabled_arrival_and_tx_guard(m):
    d=m.device;d.inject_uart(1,b'ignored');assert not d.rx[1]
    b=uart(m,1,fifo=False);d.inject_uart(1,b'xy')
    assert bytes(d.rx[1])==b'x' and m.read_register(b+0x1108)&8
    m.write_register(b+0x1120,ord('z'));assert d.tx[1]==b'z'
    m.write_register(b+0x1100,9)
    with pytest.raises(ModelError):m.write_register(b+0x1120,0)

def test_gpio_edges_group_index_and_source_clear_preserve_nvic_pending(m):
    b=0x400a0000;d=m.device
    m.write_register(b+0x1390,(1<<2)|(2<<4)|(3<<6))
    m.write_register(b+0x1028,14)
    d.set_gpio_inputs(14);assert m.read_register(b+0x1030)==10
    assert m.read_register(0x40401130)==1
    assert m.read_register(b+0x1020)==2
    assert m.read_register(0x40401130)==1
    m.write_register(b+0x1048,8)
    assert m.read_register(0x40401130)==0 and not m.irq_lines&2
    assert 17 in m.pending
    d.set_gpio_inputs(0);assert m.read_register(b+0x1030)==12
    # An externally changed output pin is driven by DOUT, not a GPIO edge.
    m.write_register(b+0x12d0,8);m.write_register(b+0x1048,0xffffffff)
    d.set_gpio_inputs(8);assert not m.read_register(b+0x1030)

def test_shared_group_sources_do_not_clear_each_others_line(m):
    for name,bit in [('WWDT0',0),('FLASHCTL',3)]:
        b=m.device.BASES[name]
        m.write_register(b+0x1028,1);m.write_register(b+0x1040,1)
    assert m.read_register(0x40401100)==1
    m.write_register(0x40081048,1)
    assert m.irq_lines&1 and m.read_register(0x40401100)==4
    m.write_register(0x400ce048,1)
    assert not m.irq_lines&1

def test_protected_reset_and_power_keys_mask_and_sticky_status(m):
    b=uart(m);d=m.device;d.inject_uart(0,b'abc')
    m.write_register(b+0x800,1);assert m.read_register(b+0x800)==1
    m.write_register(b+0x804,1);assert d.rx[0]
    m.write_register(b+0x804,0xb1000001)
    assert not d.rx[0] and m.read_register(b+0x814)&0x10000
    m.write_register(b+0x804,0xb1000002)
    assert not m.read_register(b+0x814)&0x10000
    assert m.read_register(b+0x800)==0
    with pytest.raises(UnsupportedRegister):m.read_register(b+0x804)

def test_system_reset_retains_pmu_bytes_external_state_and_memory(m):
    d=m.device;m.read_register(0x400b0220)
    for i,a in enumerate(d.RETAINED):m.write_register(a,0x123+i)
    m.write_ram(0x20000000,b'RAM');m.mutate_flash(0x800,b'FLASH')
    d.expander.expander[2]=0x5a;d.set_gpio_inputs(3)
    b=uart(m);d.inject_uart(0,b'ab');m.reset_system('sysresetreq')
    assert [m.read_register(a) for a in d.RETAINED]==[0x23,0x24,0x25,0x26]
    assert m.read(0x20000000,3)==b'RAM' and m.read(0x800,5)==b'FLASH'
    assert d.expander.expander[2]==0x5a and d.gpio_inputs==3
    assert not d.rx[0] and not m.irq_lines
    assert m.read_register(0x400b0220)==0x1b
    assert m.read_register(0x400b0220)==0
    m.reset_system('wwdt0');m.reset_system('sysresetreq')
    assert m.read_register(0x400b0220)==0x0e

def adc(m,mode=0,start=0,end=0,manual=False):
    m.write_register(0x40004800,0x26000001)
    m.write_register(0x40005100,1)
    m.write_register(0x40005108,(start<<16)|(end<<24))
    ctl=(mode<<16)|(0x100000 if manual else 0)
    m.write_register(0x40005104,ctl)
    return ctl

def test_adc_manual_sampling_sequence_aliases_and_interrupts(m):
    ctl=adc(m,1,1,2,True);d=m.device
    for i,ch in [(1,6),(2,9)]:m.write_register(0x40005180+4*i,ch)
    d.adc_inputs={6:1234,9:3456};m.write_register(0x40005028,0x600)
    m.write_register(0x40005104,ctl|0x100);m.advance(100)
    assert m.read_register(0x40005340)&1 and not m.read_register(0x40005284)
    m.write_register(0x40005104,ctl);m.advance(d.adc_delay)
    assert m.read_register(0x40005284)==m.read_register(0x4055a284)==1234
    assert m.read_register(0x40005340)&1 and m.irq_lines&(1<<4)
    m.advance(d.adc_delay)
    assert m.read_register(0x40005288)==m.read_register(0x4055a288)==3456
    assert not m.read_register(0x40005340)&1
    assert m.read_register(0x40005020)==10 and m.read_register(0x40005020)==11
    assert not m.irq_lines&(1<<4)

def test_adc_missing_sample_stuck_and_enc_abort_boundaries(m):
    ctl=adc(m,1,0,1);d=m.device;d.adc_stuck=True
    m.write_register(0x40005180,4);m.write_register(0x40005184,7)
    m.write_register(0x40005104,ctl|0x100);m.advance(100)
    assert m.read_register(0x40005340)&1
    d.adc_stuck=False
    with pytest.raises(MissingInput):m.advance(1)
    d.adc_inputs={4:765};m.write_register(0x40005100,0);m.advance(1)
    assert m.read_register(0x40005280)==765 and not d.adc_queue
    assert not m.read_register(0x40005340)&1

def test_adc_unsupported_mode_is_not_a_successful_fake_conversion(m):
    ctl=adc(m,2)
    with pytest.raises(UnsupportedRegister):m.write_register(0x40005104,ctl|0x100)

def watchdog(m,control=0x70):
    m.device.watchdog_tick_ratio=1
    m.write_register(0x40080800,0x26000001)
    m.write_register(0x40081100,0xc9000000|control)
    m.write_register(0x40081104,0xbe000000)

@pytest.mark.parametrize('address,value',[(0x40081100,0x70),(0x40081104,0),(0x40081108,0)])
def test_watchdog_invalid_key_requests_system_reset(m,address,value):
    watchdog(m);m.write_register(address,value)
    assert m._transition==('reset','wwdt0') and m.device.watchdog_violations
    assert not m.read_register(0x4008110c)&1

def test_watchdog_window_boundary_interval_irq_and_expiry(m):
    watchdog(m,0x470);d=m.device
    m.advance(31);m.write_register(0x40081108,0xa7)
    assert d.watchdog_violations[-1][1]=='closed-window'
    m.reset_system('sysresetreq');watchdog(m,0x470)
    m.advance(32);m.write_register(0x40081108,0xa7)
    assert m._transition is None
    m.advance(64);assert m._transition==('reset','wwdt0')
    m.reset_system('sysresetreq');watchdog(m,0x10070)
    m.write_register(0x40081028,1);m.advance(64)
    assert m._transition is None and m.irq_lines&1
    assert m.read_register(0x40401100)==1
    assert m.read_register(0x40081020)==1 and not m.irq_lines&1
    m.advance(64);assert m.irq_lines&1
    assert m.read_register(0x40081108)==0

def test_i2c_nack_raw_flag_latches_before_masks_are_enabled(m):
    m.write_register(0x400f1210,0x27<<1)
    m.write_register(0x400f1214,0x10007)
    assert m.read_register(0x400f1030)&0x80 and not m.irq_lines&(1<<24)
    m.write_register(0x400f1028,0x80)
    assert m.irq_lines&(1<<24) and m.read_register(0x400f1020)==8
    assert not m.irq_lines&(1<<24)

def test_flash_requires_execute_preserves_protection_and_aborts_on_reset(m):
    b=0x400cd000;before=m.read(0x800,8)
    m.write_register(b+0x11d0,0xffffffff)
    m.write_register(b+0x1104,0x42);m.write_register(b+0x1120,0x800)
    assert m.read(0x800,8)==before
    m.write_register(b+0x1100,1)
    m.advance(m.device.flash_delay)
    assert m.device.flash.events[-1][-1]==0x11 and m.read(0x800,8)==before
    m.write_register(b+0x11d0,0)
    m.write_register(b+0x1100,1)
    with pytest.raises(ModelError):m.write_register(b+0x1100,1)
    m.reset_system('sysresetreq')
    assert m.device.flash.pending is None and m.read(0x800,8)==before
    assert m.read_register(b+0x11d0)==m.metadata[b+0x11d0].reset


def test_flash_completion_is_time_driven_irq_and_nor_program_errors(m):
    b=0x400cd000;d=m.device;address=0x1000
    m.mutate_flash(address,b'abcdefgh')
    m.write_register(b+0x1028,1)
    m.write_register(b+0x1104,0x42);m.write_register(b+0x1120,address)
    m.write_register(b+0x1100,1)
    for _ in range(20):assert m.read_register(b+0x13d0)==4
    assert m.read(address,8)==b'abcdefgh' and not m.irq_lines&1
    d.flash_stuck=True;m.advance(d.flash_delay*2)
    assert m.read_register(b+0x13d0)==4 and m.read(address,8)==b'abcdefgh'
    d.flash_stuck=False;m.advance(1)
    assert m.read(address,8)==b'\xff'*8 and m.read_register(b+0x13d0)==3
    assert m.irq_lines&1 and m.read_register(0x40401100)==4
    assert m.read_register(b+0x1020)==1 and not m.irq_lines&1
    m.write_register(b+0x1104,1);m.write_register(b+0x1124,255)
    m.write_register(b+0x1130,0x11223344);m.write_register(b+0x1134,0xaabbccdd)
    m.write_register(b+0x1100,1);m.advance(d.flash_delay)
    programmed=m.read(address,8);assert programmed==bytes.fromhex('44332211ddccbbaa')
    m.write_register(b+0x1130,0xffffffff);m.write_register(b+0x1100,1)
    m.advance(d.flash_delay)
    assert m.read_register(b+0x13d0)==0x101 and m.read(address,8)==programmed
    # Address error and injected controller failure cannot mutate flash.
    m.write_register(b+0x1120,address+1);m.write_register(b+0x1100,1);m.advance(d.flash_delay)
    assert m.read_register(b+0x13d0)==0x41
    m.write_register(b+0x1120,address);m.write_register(b+0x1104,0x42)
    d.flash.fail=('erase',d.flash.counts['erase']+1)
    m.write_register(b+0x1100,1);m.advance(d.flash_delay)
    assert m.read_register(b+0x13d0)==0x1001 and m.read(address,8)==programmed

def test_resetcmd_requires_key_and_unsupported_boot_domain_stops(m):
    m.write_register(0x400b0300,0);m.write_register(0x400b0304,1)
    assert m._transition is None
    m.write_register(0x400b0304,0xe4000001)
    assert m._transition==('reset','sysresetreq')
    m.reset_system();m.write_register(0x400b0300,1)
    with pytest.raises(UnsupportedRegister):m.write_register(0x400b0304,0xe4000001)

def test_peripheral_reset_has_no_stale_shared_irq_pending(m):
    watchdog(m,0x10070);m.write_register(0x40081028,1);m.advance(64)
    assert m.irq_lines&1 and 16 in m.pending
    m.reset_system();assert not m.irq_lines and not m.pending

def test_watchdog_starts_without_feed_and_reconfiguration_is_explicit(m):
    watchdog(m);assert m.device.watchdog_feeds==0 and m.read_register(0x4008110c)&1
    m.advance(64);assert m._transition==('reset','wwdt0')
    m.reset_system();watchdog(m)
    before=m.read_register(0x40081100)
    with pytest.raises(UnsupportedRegister):m.write_register(0x40081100,0xc9010040)
    assert m.read_register(0x40081100)==before


def test_adc_sequence_results_are_independent_of_clock_step_partition(m):
    n=MCU(fixture_image())
    for machine in (m,n):
        ctl=adc(machine,1,0,3)
        for i in range(4):machine.write_register(0x40005180+4*i,i+4)
        machine.device.adc_inputs={i+4:(i+1)*777 for i in range(4)}
        machine.write_register(0x40005104,ctl|0x100)
    m.advance(m.device.adc_delay*4)
    for _ in range(4):n.advance(n.device.adc_delay)
    assert [m.read_register(0x4055a280+4*i) for i in range(4)]==[
        n.read_register(0x4055a280+4*i) for i in range(4)]
    assert not m.device.adc_queue and not n.device.adc_queue
    assert m.read_register(0x40005030)==n.read_register(0x40005030)
