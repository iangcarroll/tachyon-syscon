"""Bounded execution of full target main; only external modules are endpoints."""
from pathlib import Path
import build_runtime_scan_image as runtime
# Entry, symbol suffix, number of meaningful fixed ABI arguments.
DEPENDENCIES=[
(0x798c,'watchdog_init',0),(0x79d0,'watchdog_feed',0),(0x7b88,'fault_stage_get',0),
(0x7b78,'fault_stage_set',1),(0x7be0,'enable_mftick',0),(0x8954,'uart_init',2),
(0x59d8,'retained_load',0),(0x776c,'timer_init',0),(0x7540,'tasks_init',0),
(0x30f0,'config_init',0),(0x5b7c,'rgb_init',1),(0x7c08,'reset_cause',0),
(0x5afc,'retained_increment_boots',0),(0x5970,'powerkey_init',1),(0x5908,'powerkey_callback',2),
(0x3808,'ioexpander_init',1),(0x7c3c,'reset_cause_name',1),(0x7bfc,'cached_reason',0),
(0x7b9c,'fault_stage_name',1),(0x5ac4,'retained_modem',0),(0x66a0,'modem_mode_name',1),
(0x5af0,'retained_battery',0),(0x5b14,'retained_boots',0),(0x54cc,'power_policy_init',1),
(0x6948,'modem_init',1),(0x3114,'auto_boot',0),(0x3144,'factory_test',0),
(0x5c68,'rgb_preset',2),(0x6428,'modem_poweron',0),(0x3488,'diagnostics_poll',0),
(0x3138,'alt_powerkey',0),(0x6690,'modem_off',0),(0x5e24,'rgb_key_feedback',0),
(0x64a0,'modem_edl',0),(0x65e4,'modem_fastboot',0),(0x51c0,'power_shutdown_request',0),
(0x6720,'modem_poweroff',1),(0x6a68,'modem_poll',0),(0x75d8,'tasks_poll',0),
(0x76d8,'tasks_active',0),(0x49d0,'protocol_poll',1),(0x7f58,'gpio_config',2),
(0x77fc,'timer_wait_countflags',1),(0x80f8,'gpio_read',1),(0x8148,'gpio_attach',4),
(0x81f8,'gpio_detach',1),(0x3120,'wakeup_enabled',0),(0x77b4,'now',0),
(0x8c8c,'uart_write_buffer',3),(0x8f88,'logger',3)]

def build(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    stubs=destination/'application_endpoints.S'
    stubs.write_text('.syntax unified\n.thumb\n'+''.join(
        f'.global syscon_target_{name}\n.type syscon_target_{name},%function\n.thumb_func\nsyscon_target_{name}:\n bkpt #0\n bx lr\n'
        for name in [*(name for _,name,_ in DEPENDENCIES),'mfg_logger']))
    old=runtime.SOURCES
    try:
        runtime.SOURCES=old+['target/application_target.c','target/application_state.c','target/diagnostics_state.c','target/power_state.c','target/logger_state.c',str(stubs)]
        return runtime.build(destination)
    finally:runtime.SOURCES=old
