"""Power-key + real target timers; external environment is compiled test C."""
import hashlib,json,subprocess
from pathlib import Path
import toolchain_process
ROOT=Path(__file__).resolve().parents[1]
SOURCES=['src/power/power_key_target.c','src/scheduling/timers_target.c','src/runtime/runtime_memory.c','tests/fixtures/target/power_key_test_fixture.c']
MAPPINGS={0x570c:'edge',0x5740:'poll',0x5844:'debounce',0x5908:'callback',0x591c:'mode',0x5970:'init'}
MAPPINGS={a:'syscon_target_powerkey_'+n for a,n in MAPPINGS.items()}
def build(destination):
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    command=['arm-none-eabi-gcc','-std=gnu11','-Os','-mcpu=cortex-m0plus','-mthumb',
        '-ffreestanding','-fno-builtin','-fno-jump-tables','-nostdlib','-Wall','-Wextra','-Werror',
        '-I',str(ROOT/'include'),*[str(ROOT/s) for s in SOURCES],'-Wl,-T,'+str(ROOT/'tests/fixtures/target/emulation.ld'),
        '-Wl,-e,syscon_target_powerkey_init','-o',str(destination)]
    toolchain_process.run(command,check=True)
    inputs=SOURCES+['include/power_key_target.h','include/power_key_state.h','include/power_key_text.h','include/scheduling_state.h','include/scheduling_target.h','include/mspm0_core_target.h',
        'include/diagnostics_target.h','include/runtime_memory.h','include/syscon.h','include/timers.h',
        'tests/fixtures/target/emulation.ld','tools/build_power_key_target.py']
    destination.with_suffix('.json').write_text(json.dumps({'command':command,
        'compiler':toolchain_process.check_output(['arm-none-eabi-gcc','--version'],text=True).splitlines()[0],
        'inputs':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in inputs},
        'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'libraries':[],
        'mappings':{hex(a):n for a,n in MAPPINGS.items()},'flash_candidate':False},indent=2)+'\n')
    return destination
if __name__=='__main__':build(ROOT/'build/power-key-src/test.elf')
