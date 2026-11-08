import random
import struct
import pytest
from unicorn import UC_MEM_WRITE
from adc_uart_target_oracle import build,Pair

@pytest.fixture(scope='module')
def driver_elf(tmp_path_factory):return build(tmp_path_factory.mktemp('adc-uart-target'))

CFG=0x20000800

def pins(p):return [p.original.cpu.mem_read(0x200000f4+12*i,1)[0] for i in range(6)]
def prepare(p):
    for address in [0x40005100,0x40005104,0x40005108,0x40004808,0x40401300]:p.word(address,0xa5a55a5a)
    p.word(0x40031104,1);p.word(0x4055a280,2000);p.word(0x41c4003c,1800)


def test_adc_init_all_descriptors_truncated_ids_config_copy_and_scale_fields(driver_elf):
    p=Pair(driver_elf);rng=random.Random(0x7c54)
    for pin in pins(p):
        for high in [0,0x100,0x10000,0xffffff00]:
            cfg=rng.randbytes(12);p.put(CFG,cfg);prepare(p)
            result=p.run(0x7c54,pin|high,CFG)
            assert result==('return',p.original.u32(0xabe0)<<32)
            assert p.candidate.read(0x20000685,7)==cfg[:7]
            assert p.candidate.read(0x2000068c,4)==cfg[4:6]+b'\0\0'


def test_adc_does_not_read_original_clock_or_assertion_text(driver_elf):
    p=Pair(driver_elf)
    p.candidate.put(0xabe0,b'\xa5'*8)
    p.candidate.put(0xdee4,b'\xa5'*(0xdf49-0xdee4))
    p.put(CFG,bytes([0,0,7,0,8,7,12]));prepare(p)
    p.run(0x7c54,pins(p)[0],CFG)
    for entry in (0x7c54,0x7e7c,0x7f24):
        assert p.run(entry,255,CFG)[0]=='assert'
    assert p.run(0x7c54,pins(p)[0],0)[0]=='assert'


def test_adc_init_aliasing_copy_and_byte_rereads(driver_elf):
    p=Pair(driver_elf);rng=random.Random(23);pin=pins(p)[0]
    for config in range(0x20000680,0x20000695):
        p.put(0x20000680,rng.randbytes(40));prepare(p);p.run(0x7c54,pin,config)

@pytest.mark.parametrize('entry,line',[(0x7c54,0x15),(0x7e7c,0x83),(0x7f24,0x83)])
def test_adc_invalid_mapping_and_null_config_assertions(driver_elf,entry,line):
    p=Pair(driver_elf)
    for value in [255,511,0xffffffff]:
        assert p.run(entry,value,CFG)[0]=='assert'
        assert p.assertions[0][0][1:]==(line,0xdf28)
    if entry==0x7c54:
        assert p.run(entry,pins(p)[0],0)[0]=='assert'
        assert p.assertions[0][0][1:]==(0x16,0xdf37)
        assert p.run(entry,255,0)[0]=='assert'
        assert p.assertions[0][0][1]==0x15


def test_adc_raw_real_delay_result_mask_descriptor_channels_and_slots(driver_elf):
    p=Pair(driver_elf)
    for index,pin in enumerate(pins(p)):
        descriptor=0x200000f4+index*12
        for channel,slot,sample in [(0,0,0),(31,3,0xffffffff),(255,255,0x80001234)]:
            p.put(descriptor+8,bytes([channel,slot]));prepare(p)
            p.word(0x4055a280+slot*4,sample)
            assert p.run(0x7e7c,pin|0xffffff00)==('return',sample&0xffff)
            assert [e for e in p.events[0] if e[0]=='delay']==[('delay',32000),('delay',3200)]


def test_adc_raw_reloads_base_and_slot_across_actual_delay_execution(driver_elf):
    p=Pair(driver_elf);pin=pins(p)[0];descriptor=0x200000f4
    prepare(p);p.word(0x40007104,0xabcdef00);p.word(0x4055a28c,0x98765432)
    def change(machine,number,cycles):
        machine.put(descriptor+4,struct.pack('<I',0x40006000 if number==1 else 0x40004000))
        if number==2:machine.put(descriptor+9,b'\x03')
    p.on_delay=change
    assert p.run(0x7e7c,pin)==('return',0x5432)
    assert (UC_MEM_WRITE,0x40007104,4,0xabcdee00) in p.events[0]


def test_adc_millivolt_wrapped_signed_product_and_scaling(driver_elf):
    p=Pair(driver_elf);pin=pins(p)[0]
    for sample,scale in [(0,0),(1,3300),(4095,3300),(65535,0xffffffff),(32768,65536),
                         (65535,0x80000000),(65535,0x7fffffff),(17,0x12345678)]:
        prepare(p);p.word(0x4055a280,sample);p.word(0x2000068c,scale)
        result=p.run(0x7f24,pin)[1]
        product=(sample*scale)&0xffffffff;signed=product-(1<<32) if product&0x80000000 else product
        expected=(abs(signed)//4096)*(-1 if signed<0 else 1)
        assert result==expected&0xffffffff

@pytest.mark.parametrize('initialized',[0,1,255])
def test_adc_temperature_initialization_ready_and_factory_arithmetic(driver_elf,initialized):
    p=Pair(driver_elf)
    for sample,calibration in [(2000,1800),(0,0),(4095,4095),(65535,1),(1,0xffffffff),
                              (0x80001234,0x80000000),(1234,5678)]:
        prepare(p);p.put(0x20000694,bytes([initialized]));p.word(0x4055a280,sample);p.word(0x41c4003c,calibration)
        p.run(0x7d54)
        writes=[e for e in p.events[0] if e[0]==UC_MEM_WRITE and e[1]==0x40030804]
        assert len(writes)==(1 if initialized==0 else 0)
        assert p.candidate.u32(0x40401300)==(0xa5a55a5a&7)


def test_adc_temperature_timeout_late_ready_and_second_read_flicker(driver_elf):
    for sequence in [[0]*101,[0]*99+[1,1],[0]*100+[1],[1,0],[0,1,1]]:
        p=Pair(driver_elf);prepare(p);p.put(0x20000694,b'\x01');p.script(0x40031104,sequence)
        result=p.run(0x7d54)
        if sequence in ([0]*101,[1,0]):assert result==('return',0x80000000)
        if sequence==[0]*101:assert p.delay_count[0]==100
        if sequence==[0]*100+[1]:assert p.delay_count[0]==102


def test_adc_factory_fault_preserves_preceding_access_mode_write(driver_elf):
    p=Pair(driver_elf);prepare(p);p.put(0x20000694,b'\x01');p.run(0x7d54)
    position=next(i for i,e in enumerate(p.events[0]) if len(e)>2 and e[1]==0x41c4003c)
    q=Pair(driver_elf);prepare(q);q.put(0x20000694,b'\x01');q.fail_at=position
    assert q.run(0x7d54)[0]=='bus-fault'
    assert q.candidate.u32(0x40401300)==5


def test_adc_init_bus_fault_at_each_observable_access_and_raw_invalid_port(driver_elf):
    def setup():
        p=Pair(driver_elf);prepare(p);p.put(CFG,bytes(range(12)));return p
    p=setup();pin=pins(p)[0];p.run(0x7c54,pin,CFG)
    for position in range(len(p.events[0])):
        q=setup();q.fail_at=position
        assert q.run(0x7c54,pin,CFG)[0]=='bus-fault'
    p=setup();p.word(0x200000f8,0x30000000)
    assert p.run(0x7e7c,pin)[0]=='cpu-fault'
    p=setup();assert p.run(0x7c54,pin,0x30000000)[0]=='cpu-fault'
