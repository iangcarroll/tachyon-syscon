import random
import struct
import pytest
from unicorn import UC_MEM_WRITE
from adc_uart_target_oracle import Pair
from test_adc_target import driver_elf
CFG=0x20000800
BASES=(0x40108000,0x40100000)

def config(baud=115200,size=9,disabled=0):return struct.pack('<HHIB',0x1234,size,baud,disabled)
def prepare(p,base,rng):
    for offset in (0x1100,0x1104,0x1110,0x1114,0x1028):p.word(base+offset,rng.getrandbits(32))


def test_uart_setup_and_assertions_ignore_original_private_rom(driver_elf):
    p=Pair(driver_elf)
    p.candidate.put(0xabe8,b'\xa5'*10)
    p.candidate.put(0xe0af,b'\xa5'*(0xe0ef-0xe0af))
    p.candidate.put(0xcfb8,b'\xa5'*16)
    p.put(CFG,config())
    for port in range(2):
        assert p.run(0x8954,port,CFG)==('return',0)
        assert p.run(0x8b50,port)==('return',0)
    assert p.run(0x8954,2,CFG)[0]=='assert'
    assert p.run(0x8954,0,0)[0]=='assert'


def test_uart_init_baud_domains_real_softfloat_chain_partial_copy_and_ring_clear(driver_elf):
    p=Pair(driver_elf);rng=random.Random(0x8954)
    bauds=[0,1,2,3,30,31,32,115200,2000000,2000001,0x7fffffff,0x80000000,0xffffffff]
    for port,base in enumerate(BASES):
        for baud in bauds:
            for size,disabled in [(0,0),(1,1),(8,0),(9,255),(65535,0)]:
                prepare(p,base,rng);p.put(0x20000762+port*9,b'\x5a'*9);p.put(0x20000774+port*76,b'\xa5'*76)
                cfg=config(baud,size,disabled);p.put(CFG,cfg)
                assert p.run(0x8954,port,CFG)==('return',0)
                count=min(size,9)
                assert p.candidate.read(0x20000762+port*9,9)==cfg[:count]+b'\x5a'*(9-count)
                assert p.candidate.read(0x20000774+port*76,76)==bytes(76)


def test_uart_init_config_destination_aliases_follow_forward_copy_and_prior_reads(driver_elf):
    p=Pair(driver_elf);rng=random.Random(17)
    for address in range(0x2000075e,0x20000772):
        p.put(0x20000750,rng.randbytes(200));p.put(address,config(9600));prepare(p,BASES[0],rng)
        p.run(0x8954,0,address)


def test_uart_deinit_irq_signed_byte_domain_barriers_and_pin_remux(driver_elf):
    p=Pair(driver_elf);rng=random.Random(0x8b50)
    for irq in range(256):
        p.put(0x20000234+12,bytes([irq]));prepare(p,BASES[0],rng)
        assert p.run(0x8b50,0)==('return',0)
        barriers=[e for e in p.events[0] if e[0]=='barrier']
        assert len(barriers)==(2 if irq<128 else 0)
        writes=[e for e in p.events[0] if e[0]==UC_MEM_WRITE and e[1]==0xe000e180]
        assert len(writes)==(1 if irq<128 else 0)


def test_uart_init_irq_masking_signed_and_wrapped_irq_bits(driver_elf):
    p=Pair(driver_elf);rng=random.Random(11)
    for irq in [0,1,31,32,63,127,128,255]:
        for disabled in [0,1,255]:
            p.put(0x20000234+12,bytes([irq]));p.put(CFG,config(disabled=disabled));prepare(p,BASES[0],rng)
            p.run(0x8954,0,CFG)
            writes=[e for e in p.events[0] if e[0]==UC_MEM_WRITE and e[1]==0xe000e100]
            assert len(writes)==(1 if not disabled and irq<128 else 0)

@pytest.mark.parametrize('entry',[0x95f0,0x9638])
def test_uart_lowlevel_all_config_bytes_bit_basis_mmio_read_order_and_aliasing(driver_elf,entry):
    p=Pair(driver_elf);rng=random.Random(entry)
    for v in range(256):
        p.put(CFG,bytes([v,255-v])*5);prepare(p,BASES[0],rng);p.run(entry,BASES[0],CFG)
    for bit in range(80):
        p.put(CFG,(1<<bit).to_bytes(10,'little'));prepare(p,BASES[0],rng);p.run(entry,BASES[0],CFG)
    for offset in [0x10fc,0x1100,0x1007]:
        p.put(BASES[0]+offset,rng.randbytes(12));p.run(entry,BASES[0],BASES[0]+offset)

@pytest.mark.parametrize('entry,line',[(0x8954,0x5b),(0x8b50,0x96)])
def test_uart_invalid_port_and_null_config_assertion_order(driver_elf,entry,line):
    p=Pair(driver_elf)
    for port in [2,255,256,0x80000000,0xffffffff]:
        assert p.run(entry,port,0)[0]=='assert';assert p.assertions[0][0][1:]==(line,0xcfb8)
    if entry==0x8954:
        assert p.run(entry,0,0)[0]=='assert';assert p.assertions[0][0][1:]==(0x5c,0xdf37)


def test_uart_deinit_reloads_irq_after_mask_write_and_init_two_lcr_reads(driver_elf):
    p=Pair(driver_elf);p.script(0x20000240,[15,255]);p.run(0x8b50,0)
    assert not any(e[0]==UC_MEM_WRITE and e[1]==0xe000e280 for e in p.events[0])
    p=Pair(driver_elf);p.put(CFG,config())
    # 95f0 consumes the first LCR read; init must then consume two distinct reads.
    p.script(BASES[0]+0x1104,[0x11111111,0xaaaaaaa1,0x55555554]);p.run(0x8954,0,CFG)
    assert (UC_MEM_WRITE,BASES[0]+0x1104,4,0x55555555) in p.events[0]

@pytest.mark.parametrize('entry,args',[(0x8954,(0,CFG)),(0x8b50,(0,)),(0x95f0,(BASES[0],CFG)),(0x9638,(BASES[0],CFG))])
def test_uart_fault_at_each_memory_access_preserves_effect_prefix(driver_elf,entry,args):
    def setup():
        p=Pair(driver_elf);p.put(CFG,config());prepare(p,BASES[0],random.Random(42));return p
    p=setup();p.run(entry,*args)
    positions=[i for i,e in enumerate(p.events[0]) if len(e)==4]
    for position in positions:
        q=setup();q.fail_at=position
        assert q.run(entry,*args)[0]=='bus-fault'


def test_uart_all_configuration_copy_lengths_and_raw_pointer_boundaries(driver_elf):
    p=Pair(driver_elf)
    for size in range(11):
        cfg=config(size=size);p.put(CFG,cfg);p.put(0x20000762,b'\xa5'*9)
        p.run(0x8954,0,CFG)
        assert p.candidate.read(0x20000762,9)==cfg[:min(size,9)]+b'\xa5'*max(9-size,0)
    for address in [0x30000000,0x20000ffc]:
        p=Pair(driver_elf);assert p.run(0x8954,0,address)[0]=='cpu-fault'
    # Raw helpers have no null-pointer check; address zero is readable flash.
    for entry in [0x95f0,0x9638]:
        p=Pair(driver_elf);p.run(entry,BASES[0],0)


def test_uart_baud_every_distinct_integer_quotient_partition_boundary(driver_elf):
    # With fixed numerator 2,000,000 these intervals partition every nonzero
    # 32-bit denominator. Test both ends of every finite nonzero-quotient
    # interval; the final zero-quotient interval includes UINT32_MAX.
    p=Pair(driver_elf);numerator=2000000;baud=1;cases=[0,2000001,0xffffffff]
    while baud<=numerator:
        quotient=numerator//baud;last=numerator//quotient
        cases.extend([baud,last]);baud=last+1
    for baud in sorted(set(cases)):
        p.put(CFG,config(baud=baud,disabled=1))
        p.run(0x8954,0,CFG)
        assert p.candidate.u32(BASES[0]+0x1110)&0xffff==((numerator//baud if baud else 0)&0xffff)
        assert p.candidate.u32(BASES[0]+0x1114)&63==0
