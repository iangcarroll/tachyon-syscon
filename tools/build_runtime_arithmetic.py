"""Build runtime source replacements without linking any installed libgcc."""
import argparse,hashlib,json,subprocess
from pathlib import Path
import toolchain_process
ROOT=Path(__file__).resolve().parents[1]
FLAGS=['-mcpu=cortex-m0plus','-mthumb','-mfloat-abi=soft','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin']

def build(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    for item in json.loads((ROOT/'vendor/gcc-soft-fp/provenance.json').read_text()):
        source=ROOT/'vendor/gcc-soft-fp'/item['file']
        if hashlib.sha256(source.read_bytes()).hexdigest()!=item['sha256']:
            raise ValueError(f'Upstream source changed: {source}')
    sources=[ROOT/'src/runtime/runtime_arithmetic.c',ROOT/'src/runtime/runtime_arithmetic_abi.S',ROOT/'src/runtime/runtime_arithmetic_float.c',*sorted((ROOT/'vendor/gcc-soft-fp').glob('*.c'))]
    objects=[]
    for source in sources:
        obj=output/(source.stem+'.o');objects.append(obj)
        # Upstream generic signed/unsigned conversion macro intentionally tests
        # an unsigned input against zero; retain source and silence only that warning.
        extra=['-Wno-type-limits'] if source.name=='floatunsisf.c' else []
        toolchain_process.run(['arm-none-eabi-gcc',*FLAGS,*extra,'-I'+str(ROOT/'include'),'-I'+str(ROOT/'vendor/gcc-soft-fp'),'-c',str(source),'-o',str(obj)],check=True)
    elf=output/'runtime-arithmetic-test.elf'
    script=output/'test.ld';script.write_text('ENTRY(syscon_rt_udiv32)\nSECTIONS { . = 0x01000000; .text : { *(.text*) *(.rodata*) } .ARM.exidx : { *(.ARM.exidx*) } . = 0x21000000; .data : { *(.data*) } .bss : { *(.bss*) } }\n')
    toolchain_process.run(['arm-none-eabi-gcc',*FLAGS,'-nostdlib','-Wl,-T,'+str(script),'-Wl,-Map,'+str(output/'test.map'),*map(str,objects),'-o',str(elf)],check=True)
    inputs=[*sources,ROOT/'include/runtime_arithmetic.h',*sorted((ROOT/'vendor/gcc-soft-fp').glob('*.h'))]
    manifest={'flash_candidate':False,'installed_library_linked':False,'compiler':toolchain_process.check_output(['arm-none-eabi-gcc','--version'],text=True).splitlines()[0],'flags':FLAGS,'per_source_flags':{'vendor/gcc-soft-fp/floatunsisf.c':['-Wno-type-limits']},'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},'elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest()}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return elf

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'build/runtime-arithmetic');args=parser.parse_args();print(build(args.output))
