import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCES=['target/format_core_target.c','target/format_core_test_fixture.c','src/format.c',
    'src/runtime_arithmetic.c','target/runtime_arithmetic_abi.S','target/emulation_runtime.c']
MAPPINGS={0x8fcc:'syscon_target_format_digits',0x9028:'syscon_target_format_forward',0x9038:'syscon_target_vformat_callback'}
def build(destination):
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True);commands=[];objects=[]
    flags=['-std=c11','-Os','-mcpu=cortex-m0plus','-mthumb','-ffreestanding','-fno-builtin','-Wall','-Wextra','-Werror','-I',str(ROOT/'include')]
    for source in SOURCES:
        obj=destination.parent/(Path(source).stem+'.o');objects.append(str(obj))
        command=['arm-none-eabi-gcc',*flags,*(['-O2'] if source=='src/runtime_arithmetic.c' else []),'-c',str(ROOT/source),'-o',str(obj)]
        subprocess.run(command,check=True);commands.append(command)
    command=['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',*objects,
        '-Wl,-T,'+str(ROOT/'target/emulation.ld'),'-Wl,-e,syscon_target_vformat_callback','-o',str(destination)]
    subprocess.run(command,check=True)
    files=SOURCES+['include/format_core_target.h','include/format.h','include/runtime_arithmetic.h','target/emulation.ld','tools/build_format_core_target.py']
    destination.with_suffix('.json').write_text(json.dumps({'compile_commands':commands,'link_command':command,
        'inputs':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files},
        'elf_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
        'compiler':subprocess.check_output(['arm-none-eabi-gcc','--version'],text=True).splitlines()[0],
        'mappings':{hex(a):n for a,n in MAPPINGS.items()},'libraries':[],'flash_candidate':False},indent=2)+'\n')
    return destination
if __name__=='__main__':build(ROOT/'build/format-core-target/test.elf')
