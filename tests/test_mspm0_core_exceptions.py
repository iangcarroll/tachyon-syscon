"""ARMv6-M core state transitions; fixtures have no firmware function hooks."""
import struct
import pytest
from unicorn.arm_const import *
from mspm0.core import MCU,BusFault,Lockup,ModelError


def image(program=b'\xfe\xe7',handler=b'\x70\x47'):
    data=bytearray(1024);struct.pack_into('<II',data,0,0x20001000,0x101)
    for n in range(2,48):struct.pack_into('<I',data,n*4,0x201)
    data[0x100:0x100+len(program)]=program;data[0x200:0x200+len(handler)]=handler
    return data


def mcu(*args,**kwargs):return MCU(image(*args),peripherals=False,**kwargs)
def frame(m,bank=UC_ARM_REG_MSP):return struct.unpack('<8I',m.read(m.cpu.reg_read(bank),32))


def test_primask_blocks_delivery_but_does_not_block_wfi_wakeup():
    m=mcu(b'\x30\xbf\x01\x20\xfe\xe7');m.enabled=1
    m.cpu.reg_write(UC_ARM_REG_PRIMASK,1)
    assert m.run(10)[0]=='wfi'
    m.pend(16);m.run(2)
    assert not m.sleeping and not m.active and 16 in m.pending
    assert m.cpu.reg_read(UC_ARM_REG_R0)==1
    m.cpu.reg_write(UC_ARM_REG_PRIMASK,0);m.run(1)
    assert any(e[:2]==('exception-enter',16) for e in m.events)


def test_disabled_or_lower_priority_irq_does_not_wake_wfi():
    m=mcu(b'\x30\xbf\xfe\xe7',b'\x30\xbf\xfe\xe7')
    m.pend(16);assert m.run(10)[0]=='wfi'
    m.enabled=3;m.priorities[16]=0x40;m.priorities[17]=0xc0
    m.pending.clear();m.enter_exception(16);assert m.run(10)[0]=='wfi'
    m.pend(17);assert m.run(10)[0]=='wfi'
    m.pend(2);m.run(1);assert m.active==[16,2]


def test_level_irq_pending_latch_clear_and_return_repend():
    m=mcu();m.enabled=1
    m.set_irq_line(0,True);m.set_irq_line(0,False)
    assert 16 in m.pending
    m.write_register(0xe000e280,1);assert 16 not in m.pending
    m.set_irq_line(0,True);m.enter_exception(16)
    assert 16 not in m.pending
    m.return_exception(0xfffffff9);assert 16 in m.pending
    m.enter_exception(16);m.set_irq_line(0,False)
    m.return_exception(0xfffffff9);assert 16 not in m.pending


def test_process_stack_selection_switches_on_entry_and_return():
    m=mcu();m.cpu.reg_write(UC_ARM_REG_PSP,0x20000e04)
    m.cpu.reg_write(UC_ARM_REG_CONTROL,3)
    m.enter_exception(16)
    assert m.cpu.reg_read(UC_ARM_REG_CONTROL)==1
    assert m.cpu.reg_read(UC_ARM_REG_SP)==m.cpu.reg_read(UC_ARM_REG_MSP)
    assert frame(m,UC_ARM_REG_PSP)[7]&(1<<9)
    m.return_exception(0xfffffffd)
    assert m.cpu.reg_read(UC_ARM_REG_CONTROL)==3
    assert m.cpu.reg_read(UC_ARM_REG_SP)==0x20000e04


@pytest.mark.parametrize('token,nested',[(0xfffffff1,False),(0xfffffff9,True),(0xfffffffd,True),(0xfffffff5,False)])
def test_exception_return_rejects_inconsistent_nesting(token,nested):
    m=mcu();m.enter_exception(16)
    if nested:m.enter_exception(2)
    with pytest.raises(Lockup):m.return_exception(token)
    assert m.locked_up and m.cpu.reg_read(UC_ARM_REG_PC)==0xfffffffe


def test_exception_return_rejects_inconsistent_frame_ipsr_and_odd_pc():
    for offset,value in [(28,(1<<24)|16),(24,0x101)]:
        m=mcu();m.enter_exception(16);sp=m.cpu.reg_read(UC_ARM_REG_MSP)
        m.write_ram(sp+offset,struct.pack('<I',value))
        with pytest.raises(Lockup):m.return_exception(0xfffffff9)


def test_svc_stacks_following_instruction_and_preserves_caller_state():
    m=mcu(b'\x00\xdf\x42\x20\xfe\xe7')
    m.cpu.reg_write(UC_ARM_REG_R0,0xabcdef01);m.run(1)
    assert m.active==[11] and frame(m)[6]==0x102
    assert frame(m)[0]==0xabcdef01
    m.run(2);assert not m.active and m.cpu.reg_read(UC_ARM_REG_R0)==0x42


def test_masked_svc_escalates_to_hardfault_with_svc_return_address():
    m=mcu(b'\x00\xdf\xfe\xe7',fault_policy='hardfault')
    m.cpu.reg_write(UC_ARM_REG_PRIMASK,1);m.run(1)
    assert m.active==[3] and frame(m)[6]==0x102
    assert m.cpu.reg_read(UC_ARM_REG_PRIMASK)==1


@pytest.mark.parametrize('program,address',[(b'\x00\x68',0x20001000),(b'\x00\x68',0x20000001),(b'\x01\x60',0x100)])
def test_precise_memory_fault_delivery_stacks_faulting_pc(program,address):
    m=mcu(program+b'\xfe\xe7',fault_policy='hardfault')
    m.cpu.reg_write(UC_ARM_REG_R0,address);m.cpu.reg_write(UC_ARM_REG_R1,0x1234)
    before=bytes(m.flash);m.run(1)
    assert m.active==[3] and frame(m)[6]==0x100
    assert bytes(m.flash)==before
    strict=mcu(program);strict.cpu.reg_write(UC_ARM_REG_R0,address)
    with pytest.raises(BusFault):strict.run(1)


@pytest.mark.parametrize('program',[b'\x00\xde',b'\x40\xf2\x01\x00'])
def test_undefined_and_armv7_only_instructions_fault(program):
    m=mcu(program,fault_policy='hardfault');m.run(1)
    assert m.active==[3] and frame(m)[6]==0x100


def test_hardfault_entry_stack_failure_locks_up():
    m=mcu(b'\x00\xde',fault_policy='hardfault');m.cpu.reg_write(UC_ARM_REG_MSP,0x20000010)
    with pytest.raises(Lockup):m.run(1)
    assert m.locked_up


@pytest.mark.parametrize('exception',[2,3])
def test_fault_during_nmi_or_hardfault_locks_up(exception):
    m=mcu(b'\xfe\xe7',b'\x00\xde',fault_policy='hardfault');m.enter_exception(exception)
    with pytest.raises(Lockup):m.run(1)


def test_sysresetreq_key_and_core_reset_preserve_ram_flash():
    m=mcu();m.write_ram(0x20000120,b'retained SRAM')
    m.cpu.reg_write(UC_ARM_REG_PSP,0x20000c00);m.cpu.reg_write(UC_ARM_REG_CONTROL,2)
    m.enabled=0xffffffff;m.priorities[17]=0xc0;m.pend(17)
    m.write_register(0xe000ed10,0x16);m.write_register(0xe000e010,7)
    m.write_register(0xe000ed0c,0xfa050004)
    assert m._transition is None and m.reset_count==0
    m.write_register(0xe000ed0c,0x05fa0004);m.run(1)
    assert m.reset_count==1 and m.read(0x20000120,13)==b'retained SRAM'
    assert not m.enabled and not m.pending and not any(m.priorities)
    assert m.cpu.reg_read(UC_ARM_REG_CONTROL)==0 and m.cpu.reg_read(UC_ARM_REG_PSP)==0
    assert m.read_register(0xe000ed10)==0 and m.systick_ctrl==4
    assert m.events[-1][0]=='system-reset'


def test_sysresetreq_cpu_store_commits_transition_before_next_instruction():
    m=mcu(b'\x01\x60\x01\x22\xfe\xe7')
    m.cpu.reg_write(UC_ARM_REG_R0,0xe000ed0c);m.cpu.reg_write(UC_ARM_REG_R1,0x05fa0004)
    m.run(1)
    assert m.reset_count==1 and m.cpu.reg_read(UC_ARM_REG_PC)==0x100
    assert m.cpu.reg_read(UC_ARM_REG_R2)==0


def test_systick_noref_source_and_reload_zero_after_active_count():
    m=mcu();m.write_register(0xe000e010,3)
    assert m.read_register(0xe000e010)&4 and m.read_register(0xe000e01c)&0x80000000
    m.write_register(0xe000e014,3);m.advance(2)
    assert m.systick_current==2
    m.write_register(0xe000e014,0);m.advance(2)
    assert m.systick_current==0 and 15 in m.pending
    m.pending.clear();m.read_register(0xe000e010);m.advance(100)
    assert not m.pending and not m.countflag
    with pytest.raises(ValueError):m.advance(-1)


def test_shpr_byte_accesses_icsr_priority_and_readonly_ccr():
    m=mcu();m.write_register(0xe000ed1f,0xff,1);m.write_register(0xe000ed22,0x40,1)
    assert m.priorities[11]==0xc0 and m.priorities[14]==0x40
    assert m.read_register(0xe000ed1c)==0xc0000000
    m.pend(14);m.pend(15);m.cpu.reg_write(UC_ARM_REG_PRIMASK,1)
    assert (m.read_register(0xe000ed04)>>12)&0x1ff==15
    m.write_register(0xe000ed14,0)
    assert m.read_register(0xe000ed14)==0x208
    with pytest.raises(BusFault):m.read_register(0xe000e010,1)


def test_high_irq_line_prevents_software_pending_clear():
    m=mcu();m.set_irq_line(0,True);m.write_register(0xe000e280,1)
    assert 16 in m.pending
    m.set_irq_line(0,False);m.write_register(0xe000e280,1)
    assert 16 not in m.pending


def test_unprivileged_thread_hardware_reads_real_primask_and_reset_clears_control():
    m=mcu();m.cpu.reg_write(UC_ARM_REG_PRIMASK,1)
    m.cpu.reg_write(UC_ARM_REG_CONTROL,1);m.enabled=1;m.pend(16)
    assert m._next_exception() is None
    m.request_reset('test-reset');m.run(1)
    assert m.cpu.reg_read(UC_ARM_REG_CONTROL)==0 and m.cpu.reg_read(UC_ARM_REG_PRIMASK)==0


def test_unprivileged_ppb_access_hardfaults_using_valid_process_stack():
    m=mcu(b'\x00\x68',fault_policy='hardfault')
    m.cpu.reg_write(UC_ARM_REG_PSP,0x20000d00);m.cpu.reg_write(UC_ARM_REG_CONTROL,3)
    m.cpu.reg_write(UC_ARM_REG_R0,0xe000ed00);m.run(1)
    assert m.active==[3] and m.cpu.reg_read(UC_ARM_REG_LR)==0xfffffffd
    assert frame(m,UC_ARM_REG_PSP)[6]==0x100


def test_exception_return_missing_thumb_bit_delivers_new_hardfault_in_thread():
    m=mcu(fault_policy='hardfault');m.enter_exception(16)
    sp=m.cpu.reg_read(UC_ARM_REG_MSP);m.write_ram(sp+28,bytes(4))
    m.run(1)
    assert m.active==[3] and m.cpu.reg_read(UC_ARM_REG_LR)==0xfffffff9
    assert frame(m)[6]==0x100 and not frame(m)[7]&(1<<24)


def test_ordinary_bad_vector_thumb_bit_escalates_after_handler_entry():
    data=image();struct.pack_into('<I',data,16*4,0x200)
    m=MCU(data,peripherals=False,fault_policy='hardfault');m.enabled=1;m.pend(16)
    m.run(1,until=0x200)
    assert m.active==[16,3] and m.cpu.reg_read(UC_ARM_REG_LR)==0xfffffff1


@pytest.mark.parametrize('program',[b'\x08\xbf',b'\x00\xb1',b'\xef\xf3\x11\x80'])
def test_it_cbz_and_basepri_are_not_silently_executed_as_armv7(program):
    m=mcu(program,fault_policy='hardfault');m.run(1)
    assert m.active==[3] and frame(m)[6]==0x100


@pytest.mark.parametrize('opcode',[b'\x20\xbf',b'\x40\xbf'])
def test_unmodeled_event_instructions_stop_explicitly(opcode):
    m=mcu(opcode,fault_policy='hardfault')
    with pytest.raises(ModelError,match='WFE/SEV'):m.run(1)
    assert not m.active
