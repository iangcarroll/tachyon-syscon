import itertools,random,struct
import pytest
from unicorn import UC_PROT_READ,UC_PROT_WRITE
from flash_abi_target_oracle import Pair,build
@pytest.fixture(scope='module')
def elf(tmp_path_factory):return build(tmp_path_factory.mktemp('flash-abi-target'))
BASE=0x400cd000
DATA=0x20000900

def test_ram_executor_and_veneer_all_status_domains(elf):
    for entry in [0x20000000,0xaae0]:
        for status in range(256):
            p=Pair(elf);p.script(BASE+0x13d0,[status,3]);p.run(entry,BASE)
            assert any(0x20000000<=a<0x20000030 for a in p.machines[0].executed)
            assert any(0x20000000<=a<0x20000030 for a in p.machines[1].executed)
    for status in [0xfffffff9,0xfffffffb,0x80000001,0x80000003]:
        p=Pair(elf);p.word(BASE+0x13d0,status);assert p.run(0xaae0,BASE)==('return',status&7)

def test_direct_helpers_full_width_arguments_and_order(elf):
    rng=random.Random(0x7af4)
    for entry in [0x7af4,0x7b10,0x7b44,0x7b60]:
        for _ in range(30):
            p=Pair(elf);p.put(DATA,rng.randbytes(8));p.script(BASE+0x13d0,[0,2,4,5,6,7,0xfffffffb])
            args={0x7af4:(BASE,rng.getrandbits(32),rng.getrandbits(32)),0x7b10:(BASE,rng.getrandbits(32),DATA),0x7b44:(BASE,),0x7b60:(BASE,rng.getrandbits(32))}[entry]
            assert p.run(entry,*args)==('return',BASE if entry==0x7b44 else 3)

def test_program_aliased_input_words_and_fault_prefixes(elf):
    for data in [BASE+0x1104,BASE+0x1120,BASE+0x1124,BASE+0x1130,DATA,DATA+1]:
        p=Pair(elf);p.word(BASE+0x13d0,3);p.word(data,0x12345678);p.word(data+4,0xdeadbeef);p.run(0x7b10,BASE,0xf800,data)
    p=Pair(elf);p.word(BASE+0x13d0,3);p.run(0x7b10,BASE,0xf800,DATA);events=len(p.events[0])
    for boundary in range(events):
        p=Pair(elf);p.word(BASE+0x13d0,3);p.fail_at=boundary;assert p.run(0x7b10,BASE,0xf800,DATA)[0]=='boundary'
    p=Pair(elf);assert p.run(0x7b10,BASE,0xf800,0x60000000)[0]=='fault'

def test_error_report_all_mask_combinations(elf):
    for value in range(32):
        status=((value&15)<<4)|((value>>4)<<12)|0xa500000f
        p=Pair(elf);p.word(BASE+0x13d0,status);p.run(0x2738)

def test_fixed_ram_target_and_nontermination_controls(elf):
    p=Pair(elf)
    for m in p.machines:m.cpu.mem_protect(0x20000000,4096,UC_PROT_READ|UC_PROT_WRITE)
    assert p.run(0xaae0,BASE)[0]=='fault'
    p=Pair(elf);p.word(BASE+0x13d0,7);p.fail_at=100
    assert p.run(0x20000000,BASE)[0]=='boundary'

def test_register_triggered_erase_program_blank_pipeline(elf):
    p=Pair(elf,model=True);p.put(0xfc00,b'\0'*1024);p.put(DATA,b'\x12\x34\x56\x78\x9a\xbc\xde\xf0')
    assert p.run(0x7af4,BASE,0xfc80,64)==('return',1) # protection failure
    p.run(0x7b44,BASE);assert p.run(0x7af4,BASE,0xfc80,64)==('return',3)
    assert p.run(0x7b60,BASE,0xfc80)==('return',3)
    assert p.run(0x7b10,BASE,0xfc80,DATA)==('return',3)
    assert p.run(0x7b60,BASE,0xfc80)==('return',1)
    p.put(DATA,b'\xff'*8);assert p.run(0x7b10,BASE,0xfc80,DATA)==('return',1)
    for m in p.machines:assert bytes(m.cpu.mem_read(0xfc80,8))==b'\x12\x34\x56\x78\x9a\xbc\xde\xf0'
    assert p.models[0].pending is None

def test_controller_invalid_addresses_modes_and_injected_failure(elf):
    for address in [1,0xffff,0x10000,0xffffffff]:
        p=Pair(elf,model=True);p.run(0x7b44,BASE);p.run(0x7b10,BASE,address,DATA)
    for size in [0,1,2,64,128,0xffffffff]:
        p=Pair(elf,model=True);p.run(0x7b44,BASE);p.run(0x7af4,BASE,0xfc00,size)
    p=Pair(elf,model=True)
    for model in p.models:model.fail=('erase',1)
    p.run(0x7b44,BASE);assert p.run(0x7af4,BASE,0xfc00,64)==('return',1)

def test_base_pointer_wrap_and_fault_semantics(elf):
    for base in [BASE,BASE+0x100,0,0x60000000,0xffffffff,0xfffff000]:
        for entry,args in [(0x7af4,(0xfc00,64)),(0x7b60,(0xfc00,)),(0x7b44,())]:
            p=Pair(elf)
            if base in [BASE,BASE+0x100]:p.word(base+0x13d0,3)
            p.run(entry,base,*args)


def test_flash_status_text_is_linked_and_survives_poisoned_legacy_rom(elf):
    p=Pair(elf)
    p.machines[1].put(0xacfa,b'\xa5'*(0xadbe-0xacfa))
    for value in [0,0x10,0x20,0x40,0x80,0x1000,0x1010]:
        p.word(BASE+0x13d0,value)
        p.run(0x2738)
        assert p.events[0][-1][0]=='log'
