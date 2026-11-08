"""Compile reconstructed modules into a relocated, nonflashable ARM test ELF."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import toolchain_process

ROOT=Path(__file__).resolve().parents[1]
SOURCES=['tests/models/rgb.c','tests/models/sg560d.c','tests/models/tasks.c','tests/models/timers.c','tests/models/retained.c',
         'tests/models/application.c','tests/models/mspm0_core.c','src/runtime/format.c','tests/models/logging.c','src/runtime/runtime_memory.c',
         'tests/fixtures/target/emulation_runtime.c','tests/fixtures/target/format_wrappers.c','src/logging/logger_target.c','src/logging/logger_state.c','src/logging/logger_target_abi.S']
RUNTIME_SOURCES=['src/runtime/runtime_arithmetic.c','src/runtime/runtime_arithmetic_abi.S',
                 'src/runtime/runtime_arithmetic_float.c',
                 *sorted(str(p.relative_to(ROOT)) for p in (ROOT/'vendor/gcc-soft-fp').glob('*.c'))]
FLAGS=['-std=c11','-Wall','-Wextra','-Werror','-mcpu=cortex-m0plus','-mthumb',
       '-mfloat-abi=soft','-Os','-ffreestanding','-fno-builtin',
       '-fno-unwind-tables','-fno-asynchronous-unwind-tables']


def build(destination):
    destination=Path(destination).resolve();destination.mkdir(parents=True,exist_ok=True)
    objects=[]
    for entry in json.loads((ROOT/'vendor/gcc-soft-fp/provenance.json').read_text()):
        assert hashlib.sha256((ROOT/'vendor/gcc-soft-fp'/entry['file']).read_bytes()).hexdigest()==entry['sha256']
    for source in SOURCES+RUNTIME_SOURCES:
        obj=destination/(Path(source).stem+'.o')
        extra=['-O2'] if source in RUNTIME_SOURCES else []
        if source.startswith('vendor/gcc-soft-fp/'):extra.append('-std=gnu11')
        if Path(source).name=='floatunsisf.c':extra.append('-Wno-type-limits')
        toolchain_process.run(['arm-none-eabi-gcc',*FLAGS,*extra,'-I',str(ROOT/'include'),'-I',str(ROOT/'vendor/gcc-soft-fp'),'-c',
                        str(ROOT/source),'-o',str(obj)],check=True)
        objects.append(obj)
    elf=destination/'reconstructed-test.elf'
    toolchain_process.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-mfloat-abi=soft',
        '-nostdlib','-Wl,-T,'+str(ROOT/'tests/fixtures/target/emulation.ld'),
        '-Wl,-Map,'+str(destination/'reconstructed-test.map'),*map(str,objects),
        '-o',str(elf)],check=True)
    compiler=toolchain_process.check_output(['arm-none-eabi-gcc','--version'],text=True).splitlines()[0]
    inputs=[*SOURCES,*RUNTIME_SOURCES,'tests/fixtures/target/emulation.ld',*sorted(str(p.relative_to(ROOT)) for p in (ROOT/'include').glob('*.h')),
            *sorted(str(p.relative_to(ROOT)) for p in (ROOT/'vendor/gcc-soft-fp').glob('*.h'))]
    manifest=dict(compiler=compiler,flags=FLAGS,code_address='0x01000000',
        global_data_address='0x21000000',flash_candidate=False,
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs},
        archive_libraries=[],runtime_optimization='-O2',vendor_c_standard='gnu11',
        elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest())
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return elf


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=ROOT/'build/arm-emulation')
    args=parser.parse_args();print(build(args.output_dir))
