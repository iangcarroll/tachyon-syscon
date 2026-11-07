import struct
import pytest
from unicorn import UcError
from unicorn.arm_const import *
from mspm0.core import MCU,BusFault,MissingImage,ModelError,UnsupportedRegister
from mspm0.profile import PROFILE,registers
from inventory import load_image

def fixture_image(handler=b'\x70\x47',program=b'\xfe\xe7'):
    image=bytearray(1024);struct.pack_into('<II',image,0,0x20001000,0x101)
    for n in range(2,48):struct.pack_into('<I',image,n*4,0x201)
    image[0x100:0x100+len(program)]=program;image[0x200:0x200+len(handler)]=handler
    return image

def synthetic_board():
    # Deliberately synthetic, not a dump of this board's identity/calibration.
    m=MCU(load_image(),factory=bytes(128),nonmain=bytes(512))
    m.device.adc_inputs=dict.fromkeys(range(32),2000)
    m.device.writeonly_read_fixtures[0x400a1048]=0
    return m

def test_physical_memory_sizes_aliases_and_prefetch_guard():
    m=MCU(fixture_image(),factory=bytes(range(128)),nonmain=bytes(range(256))*2)
    assert m.read(0,0x100)==m.read(0x400000,0x100)
    assert m.read(0x41c40000,128)==m.read(0x41c50000,128)
    assert m.read(0x41c00000,512)==m.read(0x41c10000,512)
    m.mutate_flash(0x8120,b'example');assert m.read(0x408120,7)==b'example'
    for address,size in [(0xfff8,1),(0x40fff8,4),(0x20000fff,2),(0x20001000,1),
                         (0x41c00200,1),(0x41c40080,1),(0x01000000,2),(0x20010000,1)]:
        with pytest.raises(BusFault):m.read(address,size)
    with pytest.raises(BusFault):m.write_ram(0x20000fff,b'xx')
    with pytest.raises(MissingImage):MCU(fixture_image()).read(0x41c4003c,4)

def test_cpu_store_cannot_change_flash_and_peripherals_are_nonexecutable():
    # str r1,[r0]; b .
    m=MCU(fixture_image(program=b'\x01\x60\xfe\xe7'))
    m.cpu.reg_write(UC_ARM_REG_R0,0x100);m.cpu.reg_write(UC_ARM_REG_R1,0)
    before=m.read(0x100,4)
    with pytest.raises((BusFault,UcError)):m.run(2)
    assert m.read(0x100,4)==before
    m=MCU(fixture_image());m.cpu.reg_write(UC_ARM_REG_PC,0x40080001)
    with pytest.raises((BusFault,UcError)):m.run(1)

def test_svd_corrections_and_unknown_register_access_are_explicit():
    r=registers()
    assert r[0x4055a280].name.startswith('ADC0_SVT_MEMRES')
    assert 0x40ab0280 not in r
    assert PROFILE['nvic_priority_bits']==2 and not PROFILE['mpu']
    m=MCU(fixture_image())
    for address in (0x40004004,0xe000e030):
        with pytest.raises((BusFault,UnsupportedRegister)):m.read(address,4)
    with pytest.raises(UnsupportedRegister):m.read_register(0x400a1048)
    m.device.writeonly_read_fixtures[0x400a1048]=0xa5
    assert m.read_register(0x400a1048)==0xa5
    with pytest.raises(BusFault):m.write_register(0x400a1030,1)

@pytest.mark.parametrize('psp',[False,True])
@pytest.mark.parametrize('misaligned',[False,True])
@pytest.mark.parametrize('handler',[b'\x70\x47',b'\x10\xb5\x55\x24\x10\xbd'])
def test_exception_stack_frame_alignment_register_restore_and_bx_pop_return(psp,misaligned,handler):
    m=MCU(fixture_image(handler));uc=m.cpu;sp=0x20000e04 if misaligned else 0x20000e00
    bank=UC_ARM_REG_PSP if psp else UC_ARM_REG_MSP
    uc.reg_write(bank,sp);uc.reg_write(UC_ARM_REG_CONTROL,2 if psp else 0)
    regs=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12,UC_ARM_REG_LR]
    for i,r in enumerate(regs):uc.reg_write(r,0x12340000+i)
    expected=[uc.reg_read(r) for r in regs]
    m.enabled=1<<15;m.pend(31);m.enter_exception(31)
    frame=struct.unpack('<8I',m.read((sp-32)&~7,32))
    assert list(frame[:6])==expected and frame[6]==0x100
    assert bool(frame[7]&(1<<9))==misaligned
    assert uc.reg_read(UC_ARM_REG_LR)==(0xfffffffd if psp else 0xfffffff9)
    m.run(6)
    assert not m.active and uc.reg_read(bank)==sp
    assert [uc.reg_read(r) for r in regs]==expected
    assert uc.reg_read(UC_ARM_REG_XPSR)&0x1ff==0

def test_nvic_mask_priority_nested_interrupts_and_pending_coalescing():
    m=MCU(fixture_image());m.write_register(0xe000e100,3)
    m.write_register(0xe000e400,0x40c0)
    m.cpu.reg_write(UC_ARM_REG_PRIMASK,1);m.pend(16);m.pend(17)
    assert m._next_exception() is None
    m.cpu.reg_write(UC_ARM_REG_PRIMASK,0);assert m._next_exception()==17
    m.enter_exception(16);assert m._next_exception()==17
    m.enter_exception(17);assert len(m.active)==2
    m.return_exception(0xfffffff1);assert m.active==[16]
    m.return_exception(0xfffffff9);assert not m.active
    m.write_register(0xe000e180,1);m.pend(16);assert m._next_exception() is None
    m.write_register(0xe000e280,1);assert 16 not in m.pending

def test_systick_reload_period_countflag_and_interrupt_masking():
    m=MCU(fixture_image());m.write_register(0xe000e014,4);m.write_register(0xe000e018,99)
    m.write_register(0xe000e010,7);m.advance(4)
    assert 15 not in m.pending and m.systick_current==1
    m.advance(1);assert 15 in m.pending
    assert m.read_register(0xe000e010)&0x10000
    assert not m.read_register(0xe000e010)&0x10000
    m.pending.clear();m.advance(5);assert 15 in m.pending
    m.write_register(0xe000e010,5);m.pending.clear();m.advance(10)
    assert 15 not in m.pending and m.countflag

def test_wfi_wakes_only_for_eligible_interrupt_without_fake_return_address():
    m=MCU(fixture_image(program=b'\x30\xbf\xfe\xe7'))
    assert m.run(20)[0]=='wfi';assert m.cpu.reg_read(UC_ARM_REG_PC)==0x102
    m.pend(31);assert m.run(20)[0]=='wfi'
    m.enabled=1<<15;m.run(3)
    assert not m.sleeping and any(e[:2]==('exception-enter',31) for e in m.events)

def test_gpio_atomic_set_clear_and_power_key_protection():
    m=MCU(fixture_image());base=0x400a0000
    m.write_register(base+0x800,1);assert m.read_register(base+0x800)==0
    m.write_register(base+0x800,0x26000001);assert m.read_register(base+0x800)==1
    m.write_register(base+0x12d0,0xf);m.write_register(base+0x1290,3)
    m.device.gpio_inputs=0xa0
    assert m.read_register(base+0x1380)==0xa3
    m.write_register(base+0x12a0,1);m.write_register(base+0x12b0,4)
    assert m.read_register(base+0x1380)==0xa6
    m.write_register(base+0x804,0xb1000003);assert m.read_register(base+0x1280)==0
