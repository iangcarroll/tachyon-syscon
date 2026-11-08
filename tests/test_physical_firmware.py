"""Physical reset/placement experiments; fixtures are never production inputs."""
import json,re,struct,subprocess
from pathlib import Path
import pytest
from elftools.elf.elffile import ELFFile
from unicorn import *
from unicorn.arm_const import *
from build_physical_firmware import ROOT,elf_audit,emit_binary,PHYSICAL

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
#include "config_state.h"
#define W(a) (*(volatile uint32_t *)(a))
void syscon_target_timestamp_constructor(void){W(0x200002cc)=0x11223344;}
void syscon_target_queue_constructor(void){W(0x200002d8)=W(0x200002cc)^0x55667788;}
void syscon_target_uart_irq(uint32_t base){W(0x200002e0)=base;}
volatile uint32_t fixture_bss;
void syscon_target_main(void){fixture_bss++;syscon_config_state.flags[SYSCON_CONFIG_AUTO_BOOT]^=1;W(0x200002e4)=syscon_target_flash_veneer(0x400cd000);for(;;){}}
__attribute__((section(".rodata.syscon_target_commands"),used)) const uint8_t syscon_target_commands[518]={0};
'''+''.join('void '+name+'(void){}\n' for name in sorted(names))
    fixture=out/'fixture.c';fixture.write_text(source)
    inputs=[(ROOT/'target/config/config_state.c','config-state.o'),(ROOT/'target/physical/startup.c','startup.o'),(ROOT/'target/physical/firmware_version.c','version.o'),(ROOT/'target/app/runtime_init_target.c','runtime-init.o'),(ROOT/'target/drivers/flash_abi_target.c','flash.o'),(fixture,'target_config_config_storage.o')]
    objects=[]
    for source,name in inputs:
        obj=out/name;objects.append(str(obj))
        subprocess.run(['arm-none-eabi-gcc','-std=c11','-mcpu=cortex-m0plus','-mthumb','-Os','-ffreestanding','-fno-builtin','-fno-inline','-ffunction-sections','-fdata-sections','-I'+str(ROOT/'include'),'-c',str(source),'-o',str(obj)],check=True)
    elf=out/'fixture-only.elf'
    subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',*objects,'-Wl,--gc-sections','-Wl,-T,'+str(ROOT/'target/physical/firmware.ld'),'-o',str(elf)],check=True)
    binary=out/'fixture-only.bin';emit_binary(elf,binary)
    return elf,binary,elf_audit(elf)

def test_fixed_layout_vectors_relocated_data_and_sram_busy_dependencies(physical_fixture):
    elf,binary,audit=physical_fixture
    assert audit['issues']==[]
    assert audit['sections']['.ram_exec']['bytes']==48
    assert audit['sections'].get('.ram_extra',{}).get('bytes',0)==0
    assert audit['stack_headroom_bytes']==0x20001000-audit['symbols']['__extra_bss_end']
    assert audit['stack_headroom_bytes']>=1024
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
    initialized=[];entries=[]
    executor=audit['symbols']['syscon_target_flash_ram_execute']&~1
    def code(uc,address,size,_):
        assert not 0x20000000<=address<executor,'Execution entered obsolete flash executor address'
        if address==executor:entries.append(address)
        if address==main:
            initialized.append(bytes(uc.mem_read(0x20000000,4096)))
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
    assert polls==4 and visits and data_reads and len(initialized)==1 and entries==[executor]
    state=initialized[0]
    assert state[0x2cc:0x2d0]==struct.pack('<I',0x11223344)
    assert state[0x2d8:0x2dc]==struct.pack('<I',0x11223344^0x55667788)
    counter=audit['symbols']['fixture_bss']-0x20000000
    assert state[counter:counter+4]==bytes(4)
    # Unallocated SRAM is neither an initialized object nor a retained-state contract.
    assert state[0x900:0xa00]==b'\xa5'*256
    for section in ['.ram_exec','.data']:
        info=audit['sections'][section];load=next(s for s in audit['load_segments'] if s['address']==info['address'])
        assert state[info['address']-0x20000000:info['address']-0x20000000+info['bytes']]==data[load['load_address']:load['load_address']+info['bytes']]
    cache=audit['symbols']['syscon_config_state']
    assert cache>=audit['symbols']['__data_start'] and cache<audit['symbols']['__data_end']

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


def test_empty_initialized_data_does_not_emit_an_sram_sized_binary(physical_fixture,tmp_path):
    elf,_,_=physical_fixture
    # This fixture variant has no .data input. Its cache symbol is a
    # test binding; this binary is not executed or accepted as production.
    objects=[str(p) for p in elf.parent.glob('*.o') if p.name!='config-state.o']
    empty=tmp_path/'empty-data.elf'
    subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',*objects,
        '-Wl,--defsym,syscon_config_state=0x20000030','-Wl,--gc-sections',
        '-Wl,-T,'+str(ROOT/'target/physical/firmware.ld'),'-o',str(empty)],check=True)
    with empty.open('rb') as stream:
        parsed=ELFFile(stream)
        assert parsed.get_section_by_name('.data')['sh_size']==0
    binary=tmp_path/'empty-data.bin'
    emit_binary(empty,binary)
    assert binary.stat().st_size<=0xf800

def test_recovered_constant_bytes_except_explicit_pointer_relocations(physical_fixture):
    _,binary,_=physical_fixture;image=binary.read_bytes();reference=(ROOT/'firmware/syscon-1.0.52.bin').read_bytes()
    meta=json.loads((ROOT/'analysis/physical-data-manifest.json').read_text())
    relocated={a for r in meta['code_pointer_relocations'] for a in range(int(r['field'],16),int(r['field'],16)+4)}
    for segment in meta['data_segments']:
        lo,hi=int(segment['start'],16),int(segment['end_exclusive'],16)
        assert all(image[a]==reference[a] for a in range(lo,hi) if a not in relocated)

def test_audit_rejects_flash_executor_outside_copied_sram(physical_fixture,tmp_path):
    elf,_,audit=physical_fixture
    bad=tmp_path/'invalid-test-only.elf';data=bytearray(elf.read_bytes())
    with elf.open('rb') as stream:
        parsed=ELFFile(stream);table=parsed.get_section_by_name('.symtab')
        index=next(i for i,s in enumerate(table.iter_symbols()) if s.name=='syscon_target_flash_ram_execute')
        offset=table['sh_offset']+index*table['sh_entsize']+4
    struct.pack_into('<I',data,offset,audit['symbols']['syscon_target_main']);bad.write_bytes(data)
    assert 'Flash executor is not a Thumb entry in the copied executable SRAM section' in elf_audit(bad)['issues']


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
    # Constructor effects and ordering are the contract. Private object placement
    # and unallocated SRAM contents are deliberately not an ABI.
    for address in (0x200002cc,0x200002d8):
        assert bytes(reference.cpu.mem_read(address,4))==bytes(cpu.mem_read(address,4))
    cache=audit['symbols']['syscon_config_state']
    assert bytes(reference.cpu.mem_read(0x20000030,22))==bytes(cpu.mem_read(cache,22))



def test_initialized_data_load_is_aligned_after_halfword_text(physical_fixture,tmp_path):
    elf,_,_=physical_fixture
    script=(ROOT/'target/physical/firmware.ld').read_text()
    old='.text : { *(.text*) *(.rodata*) }'
    assert old in script
    script=script.replace(old,'.text : { *(.text*) *(.rodata*) . = ALIGN(4); SHORT(0); }')
    linker=tmp_path/'halfword-text.ld';linker.write_text(script)
    variant=tmp_path/'halfword-text.elf'
    subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',
        *map(str,elf.parent.glob('*.o')),'-Wl,--gc-sections','-Wl,-T,'+str(linker),
        '-o',str(variant)],check=True,capture_output=True,text=True)
    audit=elf_audit(variant)
    code=audit['sections']['.text']
    assert (code['address']+code['bytes'])%4==2
    assert audit['symbols']['__data_load']%4==0

    binary=tmp_path/'halfword-text.bin';emit_binary(variant,binary)
    image=binary.read_bytes();cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS)
    cpu.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M0)
    cpu.mem_map(0,65536);cpu.mem_write(0,image)
    cpu.mem_map(0x20000000,4096);cpu.mem_write(0x20000000,b'\xa5'*4096)
    reached=[]
    def step(uc,address,size,unused):
        if address==audit['symbols']['syscon_target_main']&~1:
            reached.append(True);uc.emu_stop()
    cpu.hook_add(UC_HOOK_CODE,step)
    sp,pc=struct.unpack_from('<II',image);cpu.reg_write(UC_ARM_REG_SP,sp);cpu.emu_start(pc,0,count=20000)
    assert reached
    symbols=audit['symbols'];size=symbols['__data_end']-symbols['__data_start']
    assert bytes(cpu.mem_read(symbols['__data_start'],size))==image[symbols['__data_load']:symbols['__data_load']+size]

    # Deliberately remove automatic LMA alignment while retaining SRAM alignment.
    # The explicit assertion must reject this independently of compiler choices.
    script=script.replace('.data : ALIGN(4)', '.data : AT(LOADADDR(.text)+SIZEOF(.text)) ALIGN(4)')
    script=script.replace('> SRAM AT> CODE :initialized','> SRAM :initialized')
    linker.write_text(script)
    result=subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',
        *map(str,elf.parent.glob('*.o')),'-Wl,--gc-sections','-Wl,-T,'+str(linker),
        '-o',str(tmp_path/'misaligned.elf')],capture_output=True,text=True)
    assert result.returncode and 'Reset data copy requires word alignment' in result.stderr


@pytest.mark.parametrize('stale_call',[False,True])
def test_linker_moved_flash_executor_is_copied_and_executes_only_sram(physical_fixture,tmp_path,stale_call):
    elf,_,original_audit=physical_fixture
    script=(ROOT/'target/physical/firmware.ld').read_text()
    needle='__ram_exec_start = .; KEEP(*(.ram_original_flash))'
    assert script.count(needle)==1
    script=script.replace(needle,'__ram_exec_start = .; '+4*'SHORT(0xde00); '+'KEEP(*(.ram_original_flash))')
    linker=tmp_path/'moved-executor.ld';linker.write_text(script)
    moved=tmp_path/'moved-executor.elf'
    objects=[str(p) for p in elf.parent.glob('*.o')]
    if stale_call:
        # Reintroduce the removed defect in source, then compile and link it.
        # A test that merely allows zero-padding fallthrough must fail this
        # negative control rather than report a successful moved executor.
        source=(ROOT/'target/drivers/flash_abi_target.c').read_text()
        call='return syscon_target_flash_ram_execute(base);'
        assert source.count(call)==1
        source=source.replace(call,'return ((uint32_t (*)(uint32_t))(uintptr_t)0x20000001u)(base);')
        broken=tmp_path/'stale-flash.c';broken.write_text(source)
        obj=tmp_path/'stale-flash.o'
        subprocess.run(['arm-none-eabi-gcc','-std=c11','-mcpu=cortex-m0plus','-mthumb',
                        '-Os','-ffreestanding','-fno-builtin','-fno-inline',
                        '-ffunction-sections','-fdata-sections','-I'+str(ROOT/'include'),
                        '-c',str(broken),'-o',str(obj)],check=True)
        objects=[path for path in objects if Path(path).name!='flash.o']+[str(obj)]
    subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',*objects,
                    '-Wl,--gc-sections','-Wl,-T,'+str(linker),'-o',str(moved)],check=True)
    audit=elf_audit(moved)
    assert not audit['issues']
    assert audit['symbols']['syscon_target_flash_ram_execute']==original_audit['symbols']['syscon_target_flash_ram_execute']+8
    binary=tmp_path/'moved-executor.bin';emit_binary(moved,binary)
    # UDF instructions make the obsolete entry trapping, not harmless padding.
    # Independently check the attempted entry before running any instruction.
    fixture=(moved,binary,audit)
    if stale_call:
        with pytest.raises(AssertionError,match='obsolete flash executor address'):
            test_reset_initializes_globals_and_flash_busy_executes_only_sram(fixture)
    else:
        test_reset_initializes_globals_and_flash_busy_executes_only_sram(fixture)
