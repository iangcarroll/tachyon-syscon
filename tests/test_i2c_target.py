import struct
import pytest
from unicorn import UC_MEM_WRITE
from i2c_pwm_target_oracle import Pair,build
@pytest.fixture(scope='module')
def elf(tmp_path_factory):return build(tmp_path_factory.mktemp('i2c-pwm-target'))
BASE=0x400f0000
CFG=0x20000800
DATA=0x20000900

def setup(elf):
    p=Pair(elf);p.put(CFG,b'\0');p.put(DATA,bytes(range(256)));p.put(0x20000760,b'\0\0')
    p.word(BASE+0x123c,0x800);return p

def test_i2c_init_modes_irq_sign_and_null_faults(elf):
    p=setup(elf)
    for mode in [0,1,255]:
        for irq in [0,24,31,32,127,128,255]:
            p.put(CFG,bytes([mode]));p.put(0x20000761,b'\x55');p.put(0x20000144,bytes([irq]));p.run(0x82f0,0,CFG)
    for bus,config in [(1,CFG),(0x100,CFG),(0xffffffff,CFG),(0,0)]:assert p.run(0x82f0,bus,config)[0]=='assert'

def test_i2c_irq_all_reason_bytes(elf):
    p=setup(elf)
    for reason in range(256):
        p.put(0x20000760,b'\0');p.word(BASE+0x1020,reason|0xabcd0000);p.run(0x8798)
        assert p.candidate.read(0x20000760,1)==bytes([int(reason in (8,11))])

def test_i2c_tx_success_zero_length_and_address_mask(elf):
    for count in [0,1,2,8,9,15,255]:
        for address in [0,0x7f,0x80,0x3ff,0xffffffff]:
            p=setup(elf);p.script(BASE+0x1218,[0,0x20,0,0x40,0] if count else [0x20,0])
            result=p.run(0x844c,0,address,DATA,count)
            assert result==('return',count)
            values=[e[3] for e in p.events[0] if e[:3]==(UC_MEM_WRITE,BASE+0x1220,4)]
            assert values==list(range(count))

def test_i2c_rx_success_payload_and_stale_error(elf):
    for count in [0,1,8,31,255]:
        for error in [0,1,255]:
            p=setup(elf);p.put(0x20000760,bytes([error]));p.script(BASE+0x1218,[0x20,0x40,0])
            p.script(BASE+0x123c,[0x801]*count+[0x800]);p.script(BASE+0x121c,[0xabcdef00+i for i in range(count)])
            if error:p.script(BASE+0x123c,[0x801,0x800])
            result=p.run(0x860c,0,0xffff,DATA,count)
            expected=(count<<32)|(0xffffffff if error and count else count if not error else 0)
            assert result==('return',expected)
            if not error:assert p.candidate.read(DATA,count)==bytes(range(count))

@pytest.mark.parametrize('entry,stage,sequence',[(0x844c,9,[0]),(0x844c,11,[0x20,0]),(0x844c,12,[0x20,0x40]),
 (0x860c,13,[0]),(0x860c,14,[0x20,0]),(0x860c,16,[0x20,0x40])])
def test_i2c_each_status_timeout_uses_real_cycle_loop(elf,entry,stage,sequence):
    p=setup(elf);p.script(BASE+0x1218,sequence);count=1 if entry==0x844c else 0
    result=p.run(entry,0,0x42,DATA,count)
    assert result==('return',(count<<32 if entry==0x860c else 0)|0xffffffff)
    assert p.delay_count[0]==10000
    logs=[e for e in p.events[0] if e[0]=='logger'];assert len(logs)==1
    assert logs[0][1][3]==0xdd7f+stage*12

def test_i2c_fifo_waits_error_injection_and_transfer_assertions(elf):
    p=setup(elf);p.script(BASE+0x1218,[0x20,0x40,0]);p.script(BASE+0x123c,[0,0,0x800,0x800,0x800])
    p.run(0x844c,0,0x42,DATA,1)
    p=setup(elf);p.script(BASE+0x1218,[0x20,0x40,0]);p.script(BASE+0x123c,[0x800,0x800,0x801,0x800]);p.run(0x860c,0,1,DATA,1)
    for entry in [0x844c,0x860c]:
        p=setup(elf);assert p.run(entry,1,1,DATA,1)[0]=='assert'
        p.put(0x20000761,b'\1');assert p.run(entry,0,1,DATA,1)[0]=='assert'

def test_i2c_error_helper_all_stages_and_busy_flushes(elf):
    for stage in [0,9,10,11,12,13,14,15,16,20,21,0xffffffff]:
        p=setup(elf);p.script(BASE+0x123c,[0,0x100,0x800,0x801,0x800]);p.run(0x82b4,0x2000013c,stage)

def test_i2c_fifo_timeouts_preserve_full_retry_count(elf):
    for entry,stage in [(0x844c,10),(0x860c,15)]:
        p=setup(elf);p.script(BASE+0x1218,[0x20,0x40,0]);p.word(BASE+0x123c,0)
        # External FIFO reset takes effect only once the recovery command writes MCTR=0.
        def after_delay(machine,number,cycles):
            if number==10000:
                idx=p.machines.index(machine);p.scripts[idx][BASE+0x123c]=__import__('collections').deque([0,0x800])
        p.on_delay=after_delay
        result=p.run(entry,0,0x22,DATA,1)
        assert result==('return',(1<<32 if entry==0x860c else 0)|0xffffffff)
        assert p.delay_count[0]==10000
        assert [e for e in p.events[0] if e[0]=='logger'][0][1][3]==0xdd7f+stage*12

def test_i2c_late_ready_descriptor_reload_and_async_error(elf):
    p=setup(elf);p.script(BASE+0x1218,[0]*9999+[0x20,0x40,0]);p.run(0x844c,0,2,DATA,1)
    assert p.delay_count[0]==9999
    p=setup(elf);p.word(BASE+0x1218,0);p.word(BASE+0x2000+0x123c,0x800)
    p.script(BASE+0x2000+0x1218,[0x20,0x40,0])
    def changed(machine,number,cycles):
        if number==1:machine.put(0x20000140,struct.pack('<I',BASE+0x2000))
    p.on_delay=changed;assert p.run(0x844c,0,2,DATA,1)==('return',1)
    for entry in [0x844c,0x860c]:
        p=setup(elf);p.script(BASE+0x1218,[0x20,0,0x40,0]);p.word(BASE+0x123c,0x800)
        def failed(machine,number,cycles):machine.put(0x20000760,b'\x01')
        p.on_delay=failed
        assert p.run(entry,0,2,DATA,1)==('return',(1<<32 if entry==0x860c else 0)|0xffffffff)

def test_i2c_invalid_data_faults_and_timeout_negative_control(elf):
    for entry in [0x844c,0x860c]:
        p=setup(elf);p.script(BASE+0x1218,[0x20,0x40,0]);p.script(BASE+0x123c,[0x801,0x800])
        assert p.run(entry,0,2,0x60000000,1)[0]=='cpu-fault'
    # A stuck flush must remain a wait; stop on the same observable read prefix.
    p=setup(elf);p.word(BASE+0x123c,0);p.fail_at=50
    assert p.run(0x82b4,0x2000013c,9)[0]=='bus-fault'

def test_i2c_byte_progress_wrap_is_not_silently_repaired(elf):
    for entry in [0x844c,0x860c]:
        for count in [256,257,0xffffffff]:
            p=setup(elf);p.script(BASE+0x1218,[0x20,0x40,0]);p.word(BASE+0x123c,0x801);p.fail_at=3000
            # Original 8-bit progress never reaches these lengths; compare a bounded
            # externally interrupted trace, rather than claiming termination.
            assert p.run(entry,0,2,DATA,count)[0]=='bus-fault'

def test_i2c_initialization_faults_at_every_observable_boundary(elf):
    p=setup(elf);p.run(0x82f0,0,CFG);events=len(p.events[0])
    for cutoff in range(events):
        # Delay markers do not represent bus accesses and are not injectable faults.
        if p.events[0][cutoff][0]=='delay':continue
        q=setup(elf);q.fail_at=cutoff;assert q.run(0x82f0,0,CFG)[0]=='bus-fault'

def test_i2c_configuration_and_payload_aliasing(elf):
    for config in [0x20000760,0x20000761,BASE+0x1200,BASE+0x1214,BASE+0x1228]:
        p=setup(elf);p.run(0x82f0,0,config)
    for entry in [0x844c,0x860c]:
        for data in [0x20000760,0x20000761,0x20000140,BASE+0x1210]:
            p=setup(elf);p.script(BASE+0x1218,[0x20,0x40,0]);p.script(BASE+0x123c,[0x801,0x800]);p.word(BASE+0x121c,0)
            p.run(entry,0,2,data,1)
