import random
import struct
import pytest
from i2c_pwm_target_oracle import Pair,build
@pytest.fixture(scope='module')
def elf(tmp_path_factory):return build(tmp_path_factory.mktemp('i2c-pwm-target'))
CFG=0x20000800
BASE=0x40080000

def randomize(p,rng):
    p.put(BASE+0x1800,rng.randbytes(256))

def test_pwm_configure_all_byte_modes_and_controls(elf):
    p=Pair(elf);rng=random.Random(0x948c)
    for mode in range(256):
        for extra in [0,1]:
            control=(mode*73)&255;period=rng.getrandbits(32)
            p.put(CFG,struct.pack('<I4B',period,mode,extra,control,0));randomize(p,rng)
            p.run(0x948c,BASE,CFG)

def test_pwm_configure_period_edges_and_aliased_configuration(elf):
    p=Pair(elf);rng=random.Random(2)
    for mode in [0,32,255]:
        for period in [0,1,2,0x7fffffff,0x80000000,0xffffffff]:
            for control in [0,1,2,255]:
                p.put(CFG,struct.pack('<I4B',period,mode,255,control,0));randomize(p,rng);p.run(0x948c,BASE,CFG)
    for offset in [0x1804,0x1808,0x1838,0x1858,0x1878,0x1888]:
        randomize(p,rng);p.run(0x948c,BASE,BASE+offset)

def test_pwm_lowlevel_masks_full_indices_and_aliasing(elf):
    p=Pair(elf);rng=random.Random(3)
    for i in [0,1,2,3,15,255,0x40000000,0x80000001,0xffffffff]:
        for _ in range(8):
            a,b=rng.getrandbits(32),rng.getrandbits(32);randomize(p,rng)
            p.run(0x941c,BASE,a,i);p.run(0x942c,BASE,a,b,i)
            p.run(0x9450,BASE,a,i);p.run(0x9470,BASE,a,b,i)
    for cfg in [CFG,BASE+0x1000,BASE+0x1008]:
        p.put(cfg,b'\xff\x20\xa5');p.run(0x9400,BASE,cfg)

def test_pwm_all_descriptors_init_enable_and_write(elf):
    p=Pair(elf)
    for i in range(3):
        desc=0x20000148+12*i;pin=p.original.cpu.mem_read(desc,1)[0];base=p.original.u32(desc+4)
        for enabled in [0,1,0xfffffffe,0xffffffff]:
            p.word(base+0x800,enabled);p.run(0x87dc,pin)
        for value in [0,1,255,256,0xffffffff]:
            p.run(0x88c0,pin,value)

def test_pwm_assertions_and_fault_prefixes(elf):
    p=Pair(elf)
    for entry in [0x87dc,0x88c0]:
        for pin in [255,256,0xffffffff]:assert p.run(entry,pin,1)[0]=='assert'
    p.put(0x20000148,b'\x1f');assert p.run(0x87dc,31)[0]=='assert'
    for entry,args in [(0x948c,(BASE,CFG)),(0x942c,(BASE,123,456,0)),(0x9400,(BASE,CFG))]:
        for cutoff in range(2):
            p=Pair(elf);p.put(CFG,struct.pack('<I4B',100,32,1,255,0));p.fail_at=cutoff
            assert p.run(entry,*args)[0]=='bus-fault'

def test_pwm_each_mask_bit_and_dynamic_read_modify_write(elf):
    p=Pair(elf)
    for bit in range(32):
        value=1<<bit
        for old in [0,0xffffffff,~value&0xffffffff]:
            p.word(BASE+0x1830,old);p.run(0x942c,BASE,value,0,0)
            p.word(BASE+0x1870,old);p.run(0x9450,BASE,value,0)
            p.word(BASE+0x1880,old);p.run(0x9470,BASE,0,value,0)
    p.put(CFG,struct.pack('<I4B',256,32,1,0xff,0))
    p.script(BASE+0x1804,[0x12345678,0xabcdef01]);p.run(0x948c,BASE,CFG)


def test_pwm_assertions_do_not_read_original_private_strings(elf):
    p=Pair(elf)
    p.candidate.put(0xe04c,b'\xa5'*(0xe0af-0xe04c))
    for entry in (0x87dc,0x88c0):
        assert p.run(entry,255,1)[0]=='assert'
    p.put(0x20000148,b'\x1f')
    assert p.run(0x87dc,31)[0]=='assert'
