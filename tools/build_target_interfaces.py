"""Compile target interfaces together and expose every unresolved link boundary.

Produces a relocatable object/archive, never a firmware image. No installed
runtime archives, original executable bytes or emulation endpoint stubs enter it.
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import toolchain_process
ROOT=Path(__file__).resolve().parents[1]
TARGETS=['physical/firmware_version.c','runtime/callback_helpers.c','config/config_state.c','config/config_helpers.c','config/config_read.c','config/config_storage.c',
    'drivers/core_helpers.c','runtime/interface_bindings.c','drivers/fault_control_target.c','drivers/fault_handlers.c','drivers/hal_helpers.c',
    'drivers/mspm0_core_target.c','drivers/gpio_state.c','drivers/uart_ring.c','drivers/uart_state.c','drivers/uart_ring_abi.S','runtime/runtime_arithmetic_abi.S','runtime/runtime_heap.c',
    'runtime/runtime_scan.c','runtime/runtime_scan_abi.S','runtime/runtime_scan_printf.c','runtime/runtime_scan_wrappers.c',
    'runtime/runtime_stdio.c','runtime/runtime_support.c','runtime/runtime_state.c','runtime/runtime_arithmetic_float.c',
    'drivers/adc_target.c','drivers/uart_hal_target.c','scheduling/timers_target.c','scheduling/tasks_target.c','power/retained_target.c',
    'app/diagnostics_target.c','app/diagnostics_state.c','app/application_target.c','app/application_state.c','logging/logger_target.c','logging/logger_state.c','logging/logger_target_abi.S',
    'power/rgb_target.c','power/power_key_target.c','power/power_policy_target.c','power/power_state.c','drivers/i2c_target.c','drivers/pwm_target.c',
    'config/config_update.c','config/config_update_abi.S','drivers/ioexpander_target.c','power/power_manager_target.c',
    'protocol/protocol_target.c','protocol/protocol_state.c','protocol/command_table_target.c','config/config_commands_target.c','protocol/control_commands_target.c','app/runtime_init_target.c',
    'runtime/format_core_target.c','modem/sg560d_target.c','modem/modem_state.c']
SOURCES=['target/'+name for name in TARGETS]+['src/runtime_memory.c','src/runtime_arithmetic.c','src/flash_controller.c','src/format.c']+sorted(str(p.relative_to(ROOT)) for p in (ROOT/'vendor/gcc-soft-fp').glob('*.c'))
FLAGS=['-std=c11','-mcpu=cortex-m0plus','-mthumb','-mfloat-abi=soft','-Os','-ffreestanding',
    '-fno-builtin','-fwrapv','-fno-inline','-fno-ipa-cp','-fno-ipa-pure-const',
    '-ffunction-sections','-fdata-sections','-fno-unwind-tables','-fno-asynchronous-unwind-tables',
    '-Wall','-Wextra','-Werror']

def build(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    objects=[]
    for source in SOURCES:
        obj=output/(source.replace('/','_').replace('.c','.o').replace('.S','.o'))
        extra=['-O2'] if source=='src/runtime_arithmetic.c' or source.startswith('vendor/gcc-soft-fp/') else []
        if source.startswith('vendor/gcc-soft-fp/'):extra+=['-std=gnu11','-I'+str(ROOT/'vendor/gcc-soft-fp')]
        if source.endswith('/floatunsisf.c'):extra+=['-Wno-type-limits']
        toolchain_process.run(['arm-none-eabi-gcc',*FLAGS,*extra,'-I'+str(ROOT/'include'),'-c',str(ROOT/source),'-o',str(obj)],check=True)
        objects.append(obj)
    combined=output/'target-interfaces.o';archive=output/'libsyscon-target-interfaces.a'
    toolchain_process.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib','-Wl,-r',*map(str,objects),'-o',str(combined)],check=True)
    # Replacing the archive avoids stale members silently surviving source-list edits.
    if archive.exists():archive.unlink()
    toolchain_process.run(['arm-none-eabi-ar','rcs',str(archive),str(combined)],check=True)
    unresolved=[]
    for line in toolchain_process.check_output(['arm-none-eabi-nm','-u',str(combined)],text=True).splitlines():
        fields=line.split()
        if fields:unresolved.append(fields[-1])
    inputs=SOURCES+[str(p.relative_to(ROOT)) for p in sorted((ROOT/'include').glob('*.h'))]
    report=dict(compiler=toolchain_process.check_output(['arm-none-eabi-gcc','--version'],text=True).splitlines()[0],
        flags=FLAGS,runtime_arithmetic_optimization='-O2',source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs},
        unresolved_symbols=sorted(unresolved),combined_object_sha256=hashlib.sha256(combined.read_bytes()).hexdigest(),
        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),archive_libraries=[],
        original_executable_bytes_included=False,emulation_endpoint_stubs_included=False,
        physical_image=False,flash_candidate=False,whole_firmware_equivalence=False,
        note='One relocatable link detects duplicate target symbols and exposes dependencies; it does not establish physical placement or source-wide equivalence.')
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'unresolved_symbols':report['unresolved_symbols'],'artifact':str(archive)},indent=2))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'build/target-interfaces');args=parser.parse_args();build(args.output)
