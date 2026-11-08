"""Build source-backed scan/print integration; no host libc or libgcc archive."""
import hashlib
import json
import subprocess
from pathlib import Path
import toolchain_process
ROOT=Path(__file__).resolve().parents[1]
SOURCES=['target/config_state.c','target/runtime_scan.c','target/runtime_scan_wrappers.c','target/runtime_scan_printf.c',
         'target/runtime_scan_abi.S','target/runtime_stdio.c','target/runtime_heap.c',
         'target/runtime_support.c','src/runtime_memory.c','src/runtime_arithmetic.c',
         'target/runtime_arithmetic_abi.S','target/emulation_runtime.c']
FLAGS=['-std=c11','-Wall','-Wextra','-Werror','-mcpu=cortex-m0plus','-mthumb',
       '-mfloat-abi=soft','-Os','-ffreestanding','-fno-builtin','-fwrapv',
       '-fno-inline','-fno-ipa-cp','-fno-ipa-pure-const',
       '-fno-unwind-tables','-fno-asynchronous-unwind-tables']
def build(destination):
    destination=Path(destination).resolve();destination.mkdir(parents=True,exist_ok=True)
    objects=[]
    for source in SOURCES:
        obj=destination/(Path(source).stem+'.o')
        extra=['-O2'] if source=='src/runtime_arithmetic.c' else []
        toolchain_process.run(['arm-none-eabi-gcc',*FLAGS,*extra,'-I',str(ROOT/'include'),'-c',str(ROOT/source),'-o',str(obj)],check=True)
        objects.append(obj)
    script=destination/'emulation.ld'
    script.write_text((ROOT/'target/emulation.ld').read_text().replace('ENTRY(syscon_rgb_scale)','ENTRY(syscon_rt_sscanf)'))
    elf=destination/'reconstructed-test.elf'
    toolchain_process.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-mfloat-abi=soft','-nostdlib',
        '-Wl,-T,'+str(script),'-Wl,-Map,'+str(destination/'reconstructed-test.map'),*map(str,objects),'-o',str(elf)],check=True)
    manifest=dict(compiler=toolchain_process.check_output(['arm-none-eabi-gcc','--version'],text=True).splitlines()[0],
        flags=FLAGS,source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in [*SOURCES,'target/emulation.ld',*sorted(str(h.relative_to(ROOT)) for h in (ROOT/'include').glob('*.h'))]},
        elf_sha256=hashlib.sha256(elf.read_bytes()).hexdigest(),flash_candidate=False,archive_libraries=[])
    (destination/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return elf
