"""Strict source-only physical-layout experiment. Never flashes a device.

A blocked build produces only objects and a manifest. No fake endpoint or
original executable payload can satisfy missing implementation symbols.
"""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
from elftools.elf.elffile import ELFFile
from build_target_interfaces import SOURCES,FLAGS,ROOT
EXTRA=['target/power_manager_target.c','target/ioexpander_target.c','target/protocol_target.c','target/command_table_target.c','target/runtime_init_target.c','target/flash_abi_target.c']
PHYSICAL=['target/physical/startup.c','target/physical/constants.S']
LINKER_SYMBOLS={'__state_bss_start','__state_bss_end','__extra_bss_end','__extra_bss_start','__physical_initial_data','__ram_exec_end','__ram_exec_load','__ram_exec_start','__ram_extra_end','__ram_extra_load','__ram_extra_start'}
LINKER_SYMBOLS.update({'__data_load','__data_start','__data_end'})
LINKER_SYMBOLS.update({'__peripheral_data_load','__peripheral_data_start',
                      '__peripheral_data_end','__peripheral_bss_start','__peripheral_bss_end'})
LINKER_SYMBOLS.update({'__irq_bss_start','__irq_bss_end'})

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def run(command):return subprocess.run(command,text=True,capture_output=True)
def emit_binary(elf_path,binary_path):
    # GNU objcopy can use an empty allocated section's SRAM VMA as its LMA,
    # padding the raw image up to SRAM even though that section has no bytes.
    with Path(elf_path).open('rb') as stream:
        empty=['--remove-section='+section.name for section in ELFFile(stream).iter_sections()
               if section['sh_flags']&2 and section['sh_size']==0]
    subprocess.run(['arm-none-eabi-objcopy','-O','binary','--gap-fill=0xff',*empty,
                    str(elf_path),str(binary_path)],check=True)
def elf_audit(path):
    with Path(path).open('rb') as stream:
        elf=ELFFile(stream);symbols={s.name:s['st_value'] for s in elf.get_section_by_name('.symtab').iter_symbols()}
        sections={s.name:{'address':s['sh_addr'],'bytes':s['sh_size'],'flags':s['sh_flags']} for s in elf.iter_sections() if s['sh_flags']&2}
        loads=[{'address':p['p_vaddr'],'load_address':p['p_paddr'],'bytes':p['p_filesz'],'memory_bytes':p['p_memsz'],'flags':p['p_flags']} for p in elf.iter_segments() if p['p_type']=='PT_LOAD']
        issues=[]
        for section in elf.iter_sections():
            if section['sh_flags']&4:
                a,n=section['sh_addr'],section['sh_size']
                if not (0xc0<=a and a+n<=0xab20 or 0x20000000<=a and a+n<=0x20000030 or 0x20000820<=a and a+n<=0x20001000):issues.append('Executable section outside declared code/RAM regions: '+section.name)
        for segment in loads:
            a,n=segment['load_address'],segment['bytes']
            if n and (a>=0xf800 or a+n>0xf800):issues.append('Load segment overlaps identity/config or exceeds physical flash')
        executor=symbols.get('syscon_target_flash_ram_execute',0)
        ram=sections.get('.ram_exec',{})
        if (not executor&1 or not ram.get('flags',0)&4 or
                not ram.get('address',0)<=(executor&~1)<ram.get('address',0)+ram.get('bytes',0)):
            issues.append('Flash executor is not a Thumb entry in the copied executable SRAM section')
        if 'syscon_flash_execute' in symbols:issues.append('Generic callback executor unexpectedly retained in direct physical image')
        callbacks=[]
        state_end=max(symbols.get('__extra_bss_end',0x20001000),
                      symbols.get('__state_bss_end',0),
                      symbols.get('__peripheral_bss_end',0),
                      symbols.get('__irq_bss_end',0),
                      symbols.get('__peripheral_data_end',0))
        return {'sections':sections,'load_segments':loads,'symbols':symbols,'issues':issues,'flash_io_words':callbacks,
                'stack_floor_address':state_end,'stack_headroom_bytes':0x20001000-state_end}

def build(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    # A failed rebuild must never leave an apparently current image behind.
    for name in ['firmware.elf','firmware.bin','firmware.map']:(output/name).unlink(missing_ok=True)
    sources=list(dict.fromkeys([*SOURCES,*EXTRA,*PHYSICAL]));objects=[];failures=[]
    forbidden=[s for s in sources if any(part in s for part in ('test_fixture','emulation_runtime','test_stub'))]
    if forbidden:raise ValueError('Test-only source forbidden in physical build: '+repr(forbidden))
    tracked=[ROOT/s for s in sources]+list((ROOT/'include').glob('*.h'))+[ROOT/'target/physical/firmware.ld',Path(__file__)]
    before={str(p.relative_to(ROOT)):digest(p) for p in tracked if p.exists()}
    for source in sources:
        obj=output/(source.replace('/','_').replace('.c','.o').replace('.S','.o'))
        extra=['-O2'] if source=='src/runtime_arithmetic.c' or source.startswith('vendor/gcc-soft-fp/') else []
        if source.startswith('vendor/gcc-soft-fp/'):extra+=['-std=gnu11','-I'+str(ROOT/'vendor/gcc-soft-fp')]
        if source.endswith('/floatunsisf.c'):extra+=['-Wno-type-limits']
        result=run(['arm-none-eabi-gcc',*FLAGS,*extra,'-DSYSCON_DIRECT_FLASH_ABI','-fstack-usage','-I'+str(ROOT/'include'),'-c',str(ROOT/source),'-o',str(obj)])
        if result.returncode:failures.append({'source':source,'error':result.stderr});continue
        objects.append(obj)
    report={'source_sha256':{s:digest(ROOT/s) for s in sources if (ROOT/s).exists()},'linker_sha256':digest(ROOT/'target/physical/firmware.ld'),'compile_failures':failures,'unresolved_symbols':[],
        'physical_mcu_identity_verified':False,'original_executable_bytes_included':False,'endpoint_stubs_included':False,'whole_image_stack_bound_proven':False,'whole_firmware_equivalence':False,'flash_candidate':False}
    if not failures:
        combined=output/'physical-inputs.o'
        result=run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib','-Wl,-r',*map(str,objects),'-o',str(combined)])
        if result.returncode:report['relocatable_link_error']=result.stderr
        else:
            unresolved=[line.split()[-1] for line in subprocess.check_output(['arm-none-eabi-nm','-u',str(combined)],text=True).splitlines() if line.split()]
            report['linker_defined_symbols']=sorted(set(unresolved)&LINKER_SYMBOLS)
            report['unresolved_symbols']=sorted(set(unresolved)-LINKER_SYMBOLS)
            report['section_size_report']=subprocess.check_output(['arm-none-eabi-size','-A',str(combined)],text=True)
        # No --unresolved-symbols=ignore-all, weak fallback stubs, or test fixtures.
        result=run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',*map(str,objects),'-Wl,-T,'+str(ROOT/'target/physical/firmware.ld'),'-Wl,--gc-sections','-Wl,-Map,'+str(output/'firmware.map'),'-o',str(output/'firmware.elf')])
        if result.returncode:report['physical_link_error']=result.stderr;(output/'firmware.elf').unlink(missing_ok=True)
        else:
            report['layout_audit']=elf_audit(output/'firmware.elf')
            if not report['layout_audit']['issues'] and not report['unresolved_symbols']:
                emit_binary(output/'firmware.elf',output/'firmware.bin')
                report['elf_sha256']=digest(output/'firmware.elf');report['binary_sha256']=digest(output/'firmware.bin')
    after={str(p.relative_to(ROOT)):digest(p) for p in tracked if p.exists()}
    report['build_input_sha256']=before;report['inputs_unchanged_during_build']=before==after
    if before!=after:
        report['changed_inputs']=[p for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p)]
        (output/'firmware.bin').unlink(missing_ok=True)
        (output/'firmware.elf').unlink(missing_ok=True)
    if report['unresolved_symbols']:(output/'firmware.elf').unlink(missing_ok=True)
    report['status']='linked-experimental' if (output/'firmware.bin').exists() else 'blocked'
    frames=[]
    for usage in sorted(output.glob('*.su')):
        for line in usage.read_text().splitlines():
            fields=line.split('\t')
            if len(fields)>=3:
                try:size=int(fields[1])
                except ValueError:continue
                frames.append({'function_location':fields[0],'bytes':size,'classification':fields[2]})
    report['compiler_stack_frames']=sorted(frames,key=lambda row:row['bytes'],reverse=True)
    report['assembly_sources_without_compiler_stack_bounds']=[s for s in sources if s.endswith(('.S','.s'))]
    report['limitations']=['No hardware operations or flash approval.','MCU identity is the unconfirmed64KiB/4KiB profile.','Per-function stack-usage files are evidence inputs, not a whole-image stack bound.','Identity/config sectors are excluded; factory/NONMAIN inputs remain external.','Source-only link/layout success is not whole-firmware equivalence.']
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','unresolved_symbols','compile_failures']},indent=2))
    return report
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'build/physical-firmware');args=parser.parse_args()
    raise SystemExit(0 if build(args.output)['status']=='linked-experimental' else 2)
