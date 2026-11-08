"""Build isolated original-ABI target modules; deliberately not a flash image."""
import hashlib,json,subprocess
from pathlib import Path
import toolchain_process
ROOT=Path(__file__).resolve().parents[1]
SOURCES=['target/scheduling/timers_target.c','target/scheduling/tasks_target.c','target/power/retained_target.c',
         'src/runtime_memory.c','target/testing/scheduling_test_fixture.c']
MAPPINGS={0x76f8:'timer_tick',0x776c:'timer_init',0x77b4:'now',0x77c0:'timer_delay',
          0x77fc:'timer_wait_countflags',0x781c:'timer_register',0x7880:'timer_unregister',
          0x7540:'tasks_init',0x7554:'tasks_submit',0x75d8:'tasks_poll',0x76d8:'tasks_active',
          0x59a0:'retained_commit',0x59d8:'retained_load',0x5a88:'retained_clear_registers',
          0x5aa8:'retained_set_modem',0x5ac4:'retained_modem',0x5ad4:'retained_set_battery',
          0x5af0:'retained_battery',0x5afc:'retained_increment_boots',0x5b14:'retained_boots'}
MAPPINGS={a:'syscon_target_'+n for a,n in MAPPINGS.items()}
def build(destination,physical_fixture=False):
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    linker='target/testing/scheduling_test.ld' if physical_fixture else 'target/testing/emulation.ld'
    command=['arm-none-eabi-gcc','-std=gnu11','-Os','-mcpu=cortex-m0plus','-mthumb',
             '-ffreestanding','-fno-builtin','-fno-jump-tables','-nostdlib','-Wall','-Wextra','-Werror',
             *(['-DSYSCON_SCHEDULING_PHYSICAL_FIXTURE'] if physical_fixture else []),
             '-I',str(ROOT/'include'),*[str(ROOT/s) for s in SOURCES],
             '-Wl,-T,'+str(ROOT/linker),'-Wl,-e,fixture_thread','-o',str(destination)]
    toolchain_process.run(command,check=True)
    files=SOURCES+['include/scheduling_target.h','include/scheduling_state.h','include/syscon.h','include/timers.h',
                   'include/runtime_memory.h',linker,'tools/build_scheduling_target.py']
    manifest={'description':'Non-production original-ABI test image with compiled test environment',
              'physical_exception_fixture':physical_fixture,
              'compiler':toolchain_process.check_output(['arm-none-eabi-gcc','--version'],text=True).splitlines()[0],
              'command':command,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
              'inputs':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},
              'mappings':{hex(k):v for k,v in MAPPINGS.items()},'libraries':[]}
    destination.with_suffix('.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return destination
if __name__=='__main__':build(ROOT/'build/scheduling-target/test.elf')
