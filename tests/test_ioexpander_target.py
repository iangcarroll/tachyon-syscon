import random
import struct
import pytest
from build_ioexpander_target import build
from ioexpander_target_oracle import Pair,E,REGS

@pytest.fixture(scope='module')
def ioexpander_elf(tmp_path_factory):return build(tmp_path_factory.mktemp('ioexpander-target')/'test.elf')

def test_ioexpander_complete_init_configure_write_read_reset_flow(ioexpander_elf):
    rng=random.Random(0x386c);p=Pair(ioexpander_elf);p.put(REGS,rng.randbytes(256))
    p.run(0x3808,1)
    for pin in range(16):
        p.put(0x20000900,bytes([1,pin&1,1]));p.run(0x386c,pin,0x20000900)
        p.run(0x3940,pin,1-(pin&1));p.run(0x39e8,pin,0x20000910)
        assert p.a.read(0x20000910,1)==bytes([1-(pin&1)])
        p.put(0x20000900,b'\0\0\0');p.run(0x386c,pin,0x20000900)
        p.run(0x39e8,pin,0x20000910)
    p.run(0x37e4)
    assert p.a.read(REGS+2,6)==b'\xff\xff\0\0\xff\xff'

def test_ioexpander_configuration_modes_noop_and_invalid_output(ioexpander_elf):
    p=Pair(ioexpander_elf);p.run(0x3808,0)
    for pin in (0,7,8,15):
        for direction in (0,0xff,0xa5):
            for output in (0,1,2,255):
                for value in (0,1,2,255):
                    for initial in (0,1,255):
                        p.put(REGS,bytes([0x5a,0xa5,0xaa,0x55,0,0,direction,direction]))
                        p.put(0x20000900,bytes([output,value,initial]));p.run(0x386c,pin,0x20000900)
                        p.run(0x3940,pin,value);p.run(0x39e8,pin,0x20000910)

@pytest.mark.parametrize('entry,args,control,count,line',[
    (0x3668,(0x12345678,0xabcdef01),4,3,0x34),
    (0x374c,(0x12345678,0xabcdef01),4,2,0x24),
    (0x36bc,(0x12345678,0x20000910),4,1,0x29),
    (0x36bc,(0x12345678,0x20000910),5,1,0x2a),
    (0x3808,(0,),6,0,0x5a)])
def test_four_retries_include_negative_two_and_terminal_assertion(ioexpander_elf,entry,args,control,count,line):
    for failures in range(5):
        for failure in (0xffffffff,0xfffffffe,0x12345678):
            p=Pair(ioexpander_elf);p.word(E+4*control,failures);p.word(E+28,failure);p.word(E+36,0xa5)
            result=p.run(entry,*args,terminal=failures==4)
            if failures==4:
                records=list(struct.iter_unpack('<6I',p.events(p.a)))
                assert records[-1][0]==0x2678 and records[-1][2]==line
                assert p.a.u32(E+60)==1
            elif entry in (0x3668,0x374c,0x36bc):assert result==args[0]

@pytest.mark.parametrize('entry,args,line,initialized',[
    (0x386c,(0,0x20000900),0x6c,0),(0x386c,(0,0),0x6d,1),
    (0x386c,(16,0x20000900),0x6d,1),(0x3940,(0,1),0x8d,0),
    (0x3940,(0xffffffff,1),0x8e,1),(0x39e8,(0,0x20000900),0x9b,0),
    (0x39e8,(16,0x20000900),0x9c,1)])
def test_preconditions_stop_without_bus_side_effects(ioexpander_elf,entry,args,line,initialized):
    p=Pair(ioexpander_elf);p.put(0x200002d0,bytes([initialized]));p.run(entry,*args,terminal=True)
    records=list(struct.iter_unpack('<6I',p.events(p.a)))
    assert len(records)==1 and records[0][0]==0x2678 and records[0][2]==line

def test_actual_nonreturning_i2c_dependency_does_not_enter_retry_loop(ioexpander_elf):
    for entry,args,dependency in [(0x3808,(1,),0x82f0),(0x374c,(6,0xff),0x844c),(0x36bc,(6,0x20000900),0x860c)]:
        p=Pair(ioexpander_elf);p.word(E+48,dependency);p.run(entry,*args,terminal=True)
        records=list(struct.iter_unpack('<6I',p.events(p.a)))
        assert sum(r[0]==dependency for r in records)==1
        assert records[-1][:4]==(0x2678,0x1234,0x5678,dependency)

def test_gpio_wrappers_pin_truncation_forward_results_and_invalid_pin(ioexpander_elf):
    for pin in (0,24,25,40,281,296,0xffffffff):
        p=Pair(ioexpander_elf);p.put(0x200002d0,b'\x01');p.word(E+52,0x87654321);p.word(E+56,0x12345678)
        bad=pin>=25 and ((pin-25)&255)>15
        p.run(0x3620,pin,terminal=bad);p.run(0x364e,pin,0xffffffff,terminal=bad)

def test_reads_follow_actual_pointer_and_configuration_mutation_between_bus_operations(ioexpander_elf):
    p=Pair(ioexpander_elf);p.run(0x3808,0);p.put(REGS,bytes([0,0,0,0,0,0,0xff,0xff]))
    p.put(0x20000900,b'\0\x01\x01');p.word(E+40,0x20000900);p.word(E+44,1)
    p.run(0x386c,0,0x20000900)
    assert p.a.read(REGS+2,1)==b'\x01' and p.a.read(REGS+6,1)==b'\xfe'
    # The final output can alias the initialized flag; no hidden state copy.
    p.run(0x39e8,1,0x200002d0);assert p.a.read(0x200002d0,1)==b'\0'
    # A null output pointer is not rejected in advance; both bus reads precede
    # its eventual CPU store fault, unlike an added null-validation branch.
    p.put(0x200002d0,b'\x01');p.run(0x39e8,1,0,terminal=True)
    assert sum(r[0]==0x860c for r in struct.iter_unpack('<6I',p.events(p.a)))==2

def test_unchecked_write_large_indices_and_nonboolean_clear(ioexpander_elf):
    p=Pair(ioexpander_elf)
    for pin in (0,7,8,15,16,255,0xffffffff):
        for initial in (0,255,0xa5):
            for value in (0,1,2,0xffffffff):
                p.put(REGS,bytes([initial])*256);p.run(0x379c,pin,value)


def test_expander_errors_do_not_depend_on_removed_rom_text(ioexpander_elf):
    p=Pair(ioexpander_elf)
    p.a.put(0xb2c7,b'\xa5'*(0xb4ac-0xb2c7))
    p.run(0x3808,1)
    # Reading an input is valid; writing it emits a diagnostic and returns -1.
    p.run(0x39e8,3,0x20000910)
    assert p.run(0x3940,3,1)==0xffffffff
    p.run(0x39e8,16,0x20000910,terminal=True)
