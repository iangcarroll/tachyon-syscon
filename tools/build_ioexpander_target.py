"""Build source-only IO expander ABI test image; no production flash output."""
import hashlib,json,subprocess
from pathlib import Path
import toolchain_process
ROOT=Path(__file__).resolve().parents[1]
SOURCES=['src/drivers/ioexpander_target.c','src/runtime/runtime_memory.c','tests/fixtures/target/ioexpander_test_fixture.c',
         'src/runtime/runtime_arithmetic.c','src/runtime/runtime_arithmetic_abi.S']
MAPPINGS={0x3620:'syscon_target_pin_read',0x364e:'syscon_target_pin_write',
          **{a:'syscon_target_ioexpander_'+n for a,n in [(0x3668,'write16'),(0x36bc,'read8'),
          (0x374c,'write8'),(0x379c,'write_unchecked'),(0x37e4,'reset'),(0x3808,'init'),
          (0x386c,'configure'),(0x3940,'write'),(0x39e8,'read')]}}
DEPENDENCIES={0x82f0:'i2c_init',0x844c:'i2c_transmit',0x860c:'i2c_receive',
              0x80f8:'gpio_read',0x8054:'gpio_write',0x2678:'assert',0x8f88:'logger'}
DEPENDENCIES={a:'syscon_target_'+n for a,n in DEPENDENCIES.items()}
def build(destination):
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    base=['arm-none-eabi-gcc','-std=gnu11','-Os','-mcpu=cortex-m0plus','-mthumb',
        '-ffreestanding','-fno-builtin','-nostdlib','-Wall','-Wextra','-Werror','-I',str(ROOT/'include'),
        ]
    commands=[];objects=[]
    for source in SOURCES:
        obj=destination.parent/(Path(source).stem+'.o');objects.append(str(obj))
        command=base+(['-O2'] if source=='src/runtime/runtime_arithmetic.c' else [])+['-c',str(ROOT/source),'-o',str(obj)]
        toolchain_process.run(command,check=True);commands.append(command)
    command=base+objects+['-Wl,-T,'+str(ROOT/'tests/fixtures/target/emulation.ld'),
        '-Wl,-e,syscon_target_ioexpander_init','-o',str(destination)]
    toolchain_process.run(command,check=True)
    inputs=SOURCES+['include/ioexpander_target.h','include/ioexpander.h','include/i2c_target.h',
        'include/mspm0_core_target.h','include/logger_target.h','include/runtime_memory.h','include/runtime_arithmetic.h',
        'tests/fixtures/target/emulation.ld','tools/build_ioexpander_target.py']
    destination.with_suffix('.json').write_text(json.dumps({'command':command,'compile_commands':commands,
        'compiler':toolchain_process.check_output(['arm-none-eabi-gcc','--version'],text=True).splitlines()[0],
        'inputs':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in inputs},
        'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'libraries':[],
        'mappings':{hex(a):n for a,n in MAPPINGS.items()},'flash_candidate':False},indent=2)+'\n')
    return destination
if __name__=='__main__':build(ROOT/'build/ioexpander-src/test.elf')
