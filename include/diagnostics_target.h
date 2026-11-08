#ifndef SYSCON_DIAGNOSTICS_TARGET_H
#define SYSCON_DIAGNOSTICS_TARGET_H
#include <stdint.h>
uint32_t syscon_target_auto_boot(void);
uint32_t syscon_target_wakeup_enabled(void);
uint32_t syscon_target_log_color(void);
uint32_t syscon_target_fastboot_enabled(void);
/* sys.demo_enabled: LED demo and suppression of normal button actions. */
uint32_t syscon_target_demo_enabled(void);
/* sys.enable_5v_when_off: header supply policy, not processor power state. */
uint32_t syscon_target_keep_5v_when_off(void);
/* Configured base intervals; callers add any mode-specific hold time. */
uint32_t syscon_target_edl_timer_seconds(void);
uint32_t syscon_target_shutdown_timer_seconds(void);
/* Exact legacy predicate: three unsigned version fields, major == 1 and
 * minor > 1. This is not a general newer-hardware or version-ordering test. */
uint32_t syscon_target_hardware_uses_dead_battery_workaround(void);
void syscon_target_diagnostics_enable(uint32_t enabled);
void syscon_target_diagnostics_poll(void);
#endif
