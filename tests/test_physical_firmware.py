"""Physical reset/placement experiments; fixtures are never production inputs."""
import json,re,struct,subprocess
from pathlib import Path
import pytest
from elftools.elf.elffile import ELFFile
from unicorn import *
from unicorn.arm_const import *
from build_physical_firmware import ROOT,elf_audit,PHYSICAL

@pytest.fixture(scope='module')
def physical_fixture(tmp_path_factory):
    out=tmp_path_factory.mktemp('physical-reset-test-only')
    meta=json.loads((ROOT/'analysis/physical-data-manifest.json').read_text())
    names={r['symbol'] for r in meta['code_pointer_relocations']}
    names-={'syscon_target_timestamp_constructor','syscon_target_queue_constructor'}
    names|={'syscon_hardfault','syscon_nmi','syscon_default_exception','syscon_target_timer_tick','syscon_target_gpio_irq','syscon_target_i2c_irq','syscon_target_hal_noop','syscon_target_logger'}
    source='''/* TEST ONLY endpoint fixture. Not a firmware implementation. */
#include <stdint.h>
#include "flash_abi_target.h"
#define W(a) (*(volatile uint32_t *)(a))
void syscon_target_timestamp_constructor(void){W(0x200002cc)=0x11223344;}
void syscon_target_queue_constructor(void){W(0x200002d8)=W(0x200002cc)^0x55667788;}
void syscon_target_uart_irq(uint32_t base){W(0x200002e0)=base;}
void syscon_target_main(void){W(0x200002e4)=syscon_target_flash_veneer(0x400cd000);for(;;){}}
__attribute__((section(".rodata.syscon_target_commands"),used)) const uint8_t syscon_target_commands[518]={0};
'''+''.join('void '+name+'(void){}\n' for name in sorted(names))
    fixture=out/'fixture.c';fixture.write_text(source)
    inputs=[(ROOT/'target/physical/startup.c','startup.o'),(ROOT/'target/physical/constants.S','constants.o'),(ROOT/'target/runtime_init_target.c','runtime-init.o'),(ROOT/'target/flash_abi_target.c','flash.o'),(fixture,'target_config_storage.o')]
    objects=[]
    for source,name in inputs:
        obj=out/name;objects.append(str(obj))
        subprocess.run(['arm-none-eabi-gcc','-std=c11','-mcpu=cortex-m0plus','-mthumb','-Os','-ffreestanding','-fno-builtin','-fno-inline','-ffunction-sections','-fdata-sections','-I'+str(ROOT/'include'),'-c',str(source),'-o',str(obj)],check=True)
    elf=out/'fixture-only.elf'
    subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',*objects,'-Wl,--gc-sections','-Wl,-T,'+str(ROOT/'target/physical/firmware.ld'),'-o',str(elf)],check=True)
    binary=out/'fixture-only.bin';subprocess.run(['arm-none-eabi-objcopy','-O','binary','--gap-fill=0xff',str(elf),str(binary)],check=True)
    return elf,binary,elf_audit(elf)

def test_fixed_layout_vectors_relocated_data_and_sram_busy_dependencies(physical_fixture):
    elf,binary,audit=physical_fixture
    assert audit['issues']==[]
    assert audit['sections']['.ram_exec']['bytes']==48
    assert audit['sections'].get('.ram_extra',{}).get('bytes',0)==0
    assert audit['stack_headroom_bytes']==2016
    data=binary.read_bytes();assert len(data)<0xf800
    vectors=struct.unpack_from('<48I',data);assert vectors[0]==0x20001000
    assert all(v==0 or v&1 for v in vectors[1:])
    meta=json.loads((ROOT/'analysis/physical-data-manifest.json').read_text())
    for r in meta['code_pointer_relocations']:
        actual=struct.unpack_from('<I',data,int(r['field'],16))[0]
        assert actual==audit['symbols'][r['symbol']]
        assert actual!=int(r['original_target'],16)
    assert data[0xf7f8:]==b'1.0.52\0'

def test_reset_initializes_globals_and_flash_busy_executes_only_sram(physical_fixture):
    elf,binary,audit=physical_fixture;data=binary.read_bytes();u=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS)
    u.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M0)
    u.mem_map(0,0x10000,UC_PROT_READ|UC_PROT_EXEC);u.mem_write(0,data)
    u.mem_map(0x20000000,4096);u.mem_write(0x20000000,b'\xa5'*4096)
    u.mem_map(0x400cd000,0x2000)
    busy=False;polls=0;visits=[];data_reads=[];main=audit['symbols']['syscon_target_main']&~1
    initialized=[]
    def code(uc,address,size,_):
        if address==main:
            initialized.append(bytes(uc.mem_read(0x20000000,0x834)))
        if busy:
            assert 0x20000000<=address<0x20001000,hex(address)
            visits.append(address)
        if polls==4 and int.from_bytes(uc.mem_read(0x200002e4,4),'little')==3:uc.emu_stop()
    def memory(uc,kind,address,size,value,_):
        nonlocal busy,polls
        if kind==UC_MEM_WRITE and address==0x400ce100:busy=True
        if kind==UC_MEM_READ and address==0x400ce3d0:
            values=[0,2,0xffffffff,3];uc.mem_write(address,struct.pack('<I',values[polls]));polls+=1
            if polls==4:busy=False
        elif kind==UC_MEM_READ and busy:
            assert 0x20000000<=address and address+size<=0x20001000,hex(address)
            data_reads.append(address)
    u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,memory)
    sp,reset=struct.unpack_from('<II',data);u.reg_write(UC_ARM_REG_SP,sp)
    u.emu_start(reset,0,count=20000)
    assert polls==4 and visits and data_reads and len(initialized)==1
    state=initialized[0]
    assert state[0x30:0x2c0]==data[0xe2e8:0xe578]
    assert state[0x2cc:0x2d0]==struct.pack('<I',0x11223344)
    assert state[0x2d8:0x2dc]==struct.pack('<I',0x11223344^0x55667788)
    assert state[0x2c0:0x2cc]==bytes(12) and state[0x2e8:0x820]==bytes(0x538)
    for section in ['.ram_exec']:
        info=audit['sections'][section];load=next(s for s in audit['load_segments'] if s['address']==info['address'])
        assert state[info['address']-0x20000000:info['address']-0x20000000+info['bytes']]==data[load['load_address']:load['load_address']+info['bytes']]

def test_constant_source_whitelist_contains_no_original_instructions():
    meta=json.loads((ROOT/'analysis/physical-data-manifest.json').read_text())
    import csv
    ranges=[(int(r['start'],16),int(r['end_inclusive'],16)+1) for r in csv.DictReader((ROOT/'analysis/function-ranges.tsv').open(),delimiter='\t')]
    for segment in meta['data_segments']:
        lo,hi=int(segment['start'],16),int(segment['end_exclusive'],16)
        assert not any(lo<end and start<hi for start,end in ranges)
    assert all('test_fixture' not in source and 'emulation_runtime' not in source for source in PHYSICAL)
    text=(ROOT/'tools/build_physical_firmware.py').read_text()
    assert "'-Wl,--unresolved-symbols=ignore-all'" not in text

def test_recovered_constant_bytes_except_explicit_pointer_relocations(physical_fixture):
    _,binary,_=physical_fixture;image=binary.read_bytes();reference=(ROOT/'firmware/syscon-1.0.52.bin').read_bytes()
    meta=json.loads((ROOT/'analysis/physical-data-manifest.json').read_text())
    relocated={a for r in meta['code_pointer_relocations'] for a in range(int(r['field'],16),int(r['field'],16)+4)}
    for segment in meta['data_segments']:
        lo,hi=int(segment['start'],16),int(segment['end_exclusive'],16)
        assert all(image[a]==reference[a] for a in range(lo,hi) if a not in relocated)

def test_audit_rejects_wrong_fixed_ram_executor_address(physical_fixture,tmp_path):
    elf,_,audit=physical_fixture
    bad=tmp_path/'invalid-test-only.elf';data=bytearray(elf.read_bytes())
    with elf.open('rb') as stream:
        parsed=ELFFile(stream);table=parsed.get_section_by_name('.symtab')
        index=next(i for i,s in enumerate(table.iter_symbols()) if s.name=='syscon_target_flash_ram_execute')
        offset=table['sh_offset']+index*table['sh_entsize']+4
    struct.pack_into('<I',data,offset,audit['symbols']['syscon_target_main']);bad.write_bytes(data)
    assert 'Original-ABI flash executor is not at SRAM20000001' in elf_audit(bad)['issues']


def test_all_known_original_code_pointers_in_imported_data_are_relocations():
    import csv
    data=(ROOT/'firmware/syscon-1.0.52.bin').read_bytes()
    entries={int(r['address'],16)|1 for r in csv.DictReader((ROOT/'analysis/functions.tsv').open(),delimiter='\t')}
    meta=json.loads((ROOT/'analysis/physical-data-manifest.json').read_text());fields={int(r['field'],16) for r in meta['code_pointer_relocations']}
    observed=set()
    for segment in meta['data_segments']:
        lo,hi=int(segment['start'],16),int(segment['end_exclusive'],16)
        for address in range(lo,hi-3):
            if struct.unpack_from('<I',data,address)[0] in entries:observed.add(address)
    assert observed==fields

def test_linker_rejects_ram_executor_slot_overflow(physical_fixture,tmp_path):
    elf,_,_=physical_fixture
    extra=tmp_path/'overflow.S';extra.write_text('.section .ram_original_flash,"ax",%progbits\n.global physical_test_overflow\nphysical_test_overflow:\n.space 16\n')
    obj=tmp_path/'overflow.o';subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-c',str(extra),'-o',str(obj)],check=True)
    result=subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',*map(str,elf.parent.glob('*.o')),str(obj),'-Wl,--undefined=physical_test_overflow','-Wl,--gc-sections','-Wl,-T,'+str(ROOT/'target/physical/firmware.ld'),'-o',str(tmp_path/'invalid.elf')],text=True,capture_output=True)
    assert result.returncode!=0
    assert 'backwards' in result.stderr or 'RAM executor exceeds' in result.stderr

def test_uart_vector_wrappers_compare_original_dependency_arguments(physical_fixture):
    from oracle import Oracle
    _,binary,audit=physical_fixture;image=binary.read_bytes()
    for original,name in [(0x8e6c,'syscon_physical_uart0_irq'),(0x8e7c,'syscon_physical_uart1_irq')]:
        reference=Oracle();calls=[];reference.hooks[0x8d70]=lambda o:calls.append(o.arg(0))
        reference.call(original)
        cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);cpu.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M0)
        cpu.mem_map(0,65536);cpu.mem_write(0,image);cpu.mem_map(0x20000000,4096)
        cpu.reg_write(UC_ARM_REG_SP,0x20001000);cpu.reg_write(UC_ARM_REG_LR,0xff01)
        cpu.emu_start(audit['symbols'][name],0xff00,count=100)
        assert cpu.reg_read(UC_ARM_REG_PC)==0xff00
        assert calls==[int.from_bytes(cpu.mem_read(0x200002e0,4),'little')]

def test_original_reset_global_initialization_and_constructor_order(physical_fixture):
    from oracle import Oracle
    _,binary,audit=physical_fixture;image=binary.read_bytes();reference=Oracle();reference.cpu.mem_write(0x20000000,b'\xa5'*4096)
    class MainReached(Exception):pass
    calls=[]
    def timestamp(o):calls.append('timestamp');o.put(0x200002cc,struct.pack('<I',0x11223344))
    def queue(o):calls.append('queue');o.put(0x200002d8,struct.pack('<I',0x11223344^0x55667788))
    def main(o):raise MainReached()
    reference.hooks.update({0x3610:timestamp,0x3ec0:queue,0x3b34:main})
    with pytest.raises(MainReached):reference.call(0x79f0)
    cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS);cpu.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M0)
    cpu.mem_map(0,65536);cpu.mem_write(0,image);cpu.mem_map(0x20000000,4096);cpu.mem_write(0x20000000,b'\xa5'*4096)
    observed=[]
    targets={audit['symbols']['syscon_target_timestamp_constructor']&~1:'timestamp',audit['symbols']['syscon_target_queue_constructor']&~1:'queue'}
    def step(uc,address,size,_):
        if address in targets:observed.append(targets[address])
        if address==(audit['symbols']['syscon_target_main']&~1):uc.emu_stop()
    cpu.hook_add(UC_HOOK_CODE,step);sp,pc=struct.unpack_from('<II',image);cpu.reg_write(UC_ARM_REG_SP,sp);cpu.emu_start(pc,0,count=20000)
    assert observed==calls==['timestamp','queue']
    left=bytearray(reference.cpu.mem_read(0x20000030,0x7f0));right=bytearray(cpu.mem_read(0x20000030,0x7f0))
    for ram,original,name in [(0x58,0x8fa1,'syscon_target_mfg_logger'),(0xf0,0x5edd,'syscon_target_sg560d_printf')]:
        assert struct.unpack_from('<I',right,ram-0x30)[0]==audit['symbols'][name]
        struct.pack_into('<I',right,ram-0x30,original)
    assert left==right


def test_legacy_format_nul_is_source_defined_read_only_non_executable(physical_fixture):
    elf,binary,audit=physical_fixture
    compatibility=audit['sections']['.legacy_format_nul']
    assert compatibility=={'address':0x2919,'bytes':1,'flags':2}
    assert binary.read_bytes()[0x2919]==0
    assert not any(s['flags']&4 and s['address']<=0x2919<s['address']+s['bytes'] for s in audit['sections'].values())
    with elf.open('rb') as stream:
        parsed=ELFFile(stream)
        containing=[p for p in parsed.iter_segments() if p['p_type']=='PT_LOAD' and p['p_vaddr']<=0x2919<p['p_vaddr']+p['p_filesz']]
        assert len(containing)==1 and containing[0]['p_flags']==4


@pytest.mark.parametrize('mutation',['byte','address','write','execute'])
def test_audit_rejects_broken_legacy_format_data(physical_fixture,tmp_path,mutation):
    elf,_,_=physical_fixture;data=bytearray(elf.read_bytes())
    with elf.open('rb') as stream:
        parsed=ELFFile(stream)
        index=next(i for i,s in enumerate(parsed.iter_sections()) if s.name=='.legacy_format_nul')
        section=parsed.get_section(index);header=parsed['e_shoff']+index*parsed['e_shentsize']
        if mutation=='byte':data[section['sh_offset']]=1
        elif mutation=='address':struct.pack_into('<I',data,header+12,0x2918)
        else:struct.pack_into('<I',data,header+8,section['sh_flags']|({'write':1,'execute':4}[mutation]))
    bad=tmp_path/'invalid-nul.elf';bad.write_bytes(data)
    assert 'Legacy format NUL must be read-only non-executable zero byte at2919' in elf_audit(bad)['issues']


def test_linker_rejects_early_text_overlapping_legacy_data(physical_fixture,tmp_path):
    elf,_,_=physical_fixture
    source=tmp_path/'overflow.S';source.write_text('.section .text.physical_test_early_overflow,"ax",%progbits\n.global physical_test_early_overflow\nphysical_test_early_overflow:\n.space 0x2900\n')
    obj=tmp_path/'target_runtime_arithmetic_float.o'
    subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-c',str(source),'-o',str(obj)],check=True)
    result=subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',*map(str,elf.parent.glob('*.o')),str(obj),'-Wl,--undefined=physical_test_early_overflow','-Wl,--gc-sections','-Wl,-T,'+str(ROOT/'target/physical/firmware.ld'),'-o',str(tmp_path/'invalid-overlap.elf')],text=True,capture_output=True)
    assert result.returncode!=0 and 'Early text overlaps legacy format NUL' in result.stderr


def test_audit_rejects_executable_legacy_load_segment(physical_fixture,tmp_path):
    elf,_,_=physical_fixture;data=bytearray(elf.read_bytes())
    with elf.open('rb') as stream:
        parsed=ELFFile(stream)
        index=next(i for i,p in enumerate(parsed.iter_segments()) if p['p_type']=='PT_LOAD' and p['p_vaddr']<=0x2919<p['p_vaddr']+p['p_filesz'])
        offset=parsed['e_phoff']+index*parsed['e_phentsize']+24
        struct.pack_into('<I',data,offset,5)
    bad=tmp_path/'invalid-exec-nul.elf';bad.write_bytes(data)
    assert 'Legacy format NUL must have a read-only non-executable load segment' in elf_audit(bad)['issues']
