"""Compiler memset uses one production implementation with matching memory effects."""
import gc
import random
import pytest
from elftools.elf.elffile import ELFFile
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.arm_const import (
    UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
    UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
    UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,
    UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_APSR,
)
from build_physical_firmware import build
from emulate import from_scenario
from rebuilt_system import SCENARIO
from inventory import load_image

RAM=0x20000000
SP=RAM+0xf80
RETURN=0x10000
REGISTERS=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,
           UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,
           UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,
           UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_APSR]

@pytest.fixture(scope='module')
def physical(tmp_path_factory):
    directory=tmp_path_factory.mktemp('memset-binding')
    manifest=build(directory)
    assert manifest['status']=='linked-experimental'
    assert manifest['inputs_unchanged_during_build']
    assert not manifest['unresolved_symbols'] and not manifest['endpoint_stubs_included']
    with (directory/'firmware.elf').open('rb') as stream:
        elf=ELFFile(stream);table=elf.get_section_by_name('.symtab')
        leaf=table.get_symbol_by_name('syscon_rt_memset')[0]
        alias=table.get_symbol_by_name('memset')[0]
        def body(symbol):
            section=elf.get_section(symbol['st_shndx']);offset=(symbol['st_value']&~1)-section['sh_addr']
            return section.data()[offset:offset+symbol['st_size']]
        info=dict(leaf_address=leaf['st_value'],alias_address=alias['st_value'],
                  leaf_body=body(leaf),alias_body=body(alias),binding=alias['st_info']['bind'])
    return (directory/'firmware.bin').read_bytes(),info

@pytest.fixture(scope='module',autouse=True)
def retained_engines():
    gc.collect();engines=[]
    yield engines
    engines.clear();gc.collect()


def test_physical_compiler_binding_is_same_leaf_address_and_body(physical):
    _,info=physical
    assert info['binding']=='STB_WEAK'
    assert info['alias_address']==info['leaf_address']
    assert info['alias_body']==info['leaf_body']


def execute(image,entry,initial,registers,owners):
    machine,_=from_scenario(SCENARIO,image);owners.append(machine);cpu=machine.cpu
    cpu.mem_write(RAM,initial)
    for register,value in registers.items():cpu.reg_write(register,value)
    writes=[]
    def observe(uc,access,address,size,value,user):
        writes.append((address,size,value&((1<<(size*8))-1)))
    cpu.hook_add(UC_HOOK_MEM_WRITE,observe,begin=RAM,end=RAM+4095)
    # Direct function boundary: no patched instruction, return stub or function
    # replacement. Stop before fetching at the supplied common return address.
    cpu.emu_start(entry|1,RETURN,count=50000)
    assert cpu.reg_read(UC_ARM_REG_PC)==RETURN
    return bytes(cpu.mem_read(RAM,4096)),tuple(cpu.reg_read(r) for r in REGISTERS),writes


@pytest.mark.parametrize('offset,length',[
    (0,0),(0x400,0),(0xf78,0),
    (0,1),(0xfff,1),(0x401,31),(0x401,32),(0x534,216),
    (0xf78,8),(0xf70,32),(0xf80,16),(0,4096),
])
@pytest.mark.parametrize('value',[0,0xff,0x12345678,0xffffffff])
def test_actual_binding_return_memory_and_ordered_writes(physical,retained_engines,offset,length,value):
    binary,info=physical;rng=random.Random((offset<<32)^length^value)
    initial=rng.randbytes(4096)
    registers={r:rng.getrandbits(32) for r in REGISTERS[:13]}
    registers.update({UC_ARM_REG_R0:RAM+offset,UC_ARM_REG_R1:value,UC_ARM_REG_R2:length,
                      UC_ARM_REG_SP:SP,UC_ARM_REG_LR:RETURN|1,UC_ARM_REG_APSR:rng.getrandbits(4)<<28})
    original=execute(load_image(),0x975a,initial,registers,retained_engines)
    rebuilt=execute(binary,info['alias_address'],initial,registers,retained_engines)
    assert rebuilt[0]==original[0] and rebuilt[2]==original[2]
    # Return value, callee-saved registers, restored SP and return destination
    # are interface obligations. Scratch registers, LR and flags are not.
    observed=[0,*range(4,12),13,15]
    assert [rebuilt[1][i] for i in observed]==[original[1][i] for i in observed]
    expected=bytearray(initial);expected[offset:offset+length]=bytes([value&255])*length
    assert rebuilt[0]==bytes(expected)
    assert len(rebuilt[2])==length
    assert [address for address,size,byte in rebuilt[2]]==list(range(RAM+offset,RAM+offset+length))
    assert all(size==1 for address,size,byte in rebuilt[2])
