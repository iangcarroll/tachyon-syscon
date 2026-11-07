"""Source-linked config commands and flash storage; only getters/watchdog leaves."""
from pathlib import Path
import config_helpers_oracle as config
MAPPINGS={0x3fdc:'cmd_config_internal',0x4490:'cmd_config_id_find',0x44dc:'cmd_config_find',
0x4528:'config_dump',0x45e0:'cmd_config_id_dump',0x45ec:'cmd_config_dump',0x45f8:'cmd_config_id_erase',
0x4638:'cmd_config_id_get',0x4684:'cmd_config_id_set',0x46d4:'cmd_config_erase',
0x4714:'cmd_config_get',0x4760:'cmd_config_set'}
GETTERS={0x3114:'auto_boot',0x3120:'wakeup_enabled',0x312c:'log_color',0x3138:'alt_powerkey',
0x3144:'factory_test',0x3150:'modem_always_on',0x315c:'powerkey_long_seconds',0x3178:'powerkey_extra_seconds'}
def build(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    trap=destination/'command_leaves.S';trap.write_text('.syntax unified\n.thumb\n'+''.join(
        f'.global syscon_target_{name}\n.type syscon_target_{name},%function\n.thumb_func\nsyscon_target_{name}:\n bkpt #0\n bx lr\n'
        for name in GETTERS.values()))
    feed=destination/'watchdog.c'
    feed.write_text('#include <stdint.h>\nuint32_t syscon_target_watchdog_feed(void){*(volatile uint32_t*)0x40081108=0xa7;return 0;}\n')
    old=config.runtime.SOURCES
    try:
        config.runtime.SOURCES=old+['target/config_commands_target.c',str(trap),str(feed)]
        return config.build(destination)
    finally:config.runtime.SOURCES=old
