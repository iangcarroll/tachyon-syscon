"""Source policy target and explicit original-ABI module endpoints."""
from pathlib import Path
import toolchain_process
import subprocess
ROOT=Path(__file__).resolve().parents[1]
MAPPINGS={0x5358:'power_report',0x54cc:'power_policy_init',0x559c:'power_minimum_update',
          0x55b4:'power_minimum_reset',0x55c4:'power_minimum',0x55dc:'shutdown_set',
          0x562c:'shutdown_reason',0x5638:'shutdown_elapsed',0x5670:'shutdown_stale',
          0x567c:'shutdown_active',0x5694:'shutdown_poll'}
DEPENDENCIES={0x4c50:('power_measure',1),0x4ca8:('power_battery_route',0),
0x4d00:('power_vbus_route',0),0x4d9c:('power_header_route',0),0x4d58:('power_battery_id',0),
0x4df4:('power_ntc',0),0x4ec4:('power_boost',0),0x3620:('pin_read',1),
0x5af0:('retained_battery',0),0x77b4:('now',0),0x7c54:('adc_init',2),
0x386c:('ioexpander_configure',2),0x8f88:('logger',3),0x8fa0:('mfg_logger',1)}
def build(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    stub=destination/'policy_endpoints.S';stub.write_text('.syntax unified\n.thumb\n'+''.join(
        f'.global syscon_target_{name}\n.type syscon_target_{name},%function\n.thumb_func\nsyscon_target_{name}:\n bkpt #0\n bx lr\n'
        for name,_ in DEPENDENCIES.values()))
    binding=destination/'memory.c'
    binding.write_text('#include "runtime_memory.h"\nvoid *memcpy(void *d,const void *s,unsigned n){return syscon_rt_memcpy(d,s,n); }\n')
    elf=destination/'policy.elf'
    toolchain_process.run(['arm-none-eabi-gcc','-std=c11','-Os','-mcpu=cortex-m0plus','-mthumb',
        '-ffreestanding','-fno-builtin','-nostdlib','-Wall','-Wextra','-Werror',
        '-I'+str(ROOT/'include'),str(ROOT/'target/power_policy_target.c'),str(ROOT/'src/runtime_memory.c'),str(binding),str(stub),
        '-Wl,-T,'+str(ROOT/'target/emulation.ld'),'-Wl,-e,syscon_target_power_policy_init','-o',str(elf)],check=True)
    return elf
