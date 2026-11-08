#ifndef SYSCON_DIAGNOSTICS_TARGET_H
#define SYSCON_DIAGNOSTICS_TARGET_H
#include <stdint.h>
uint32_t syscon_target_auto_boot(void);
uint32_t syscon_target_wakeup_enabled(void);
uint32_t syscon_target_log_color(void);
uint32_t syscon_target_alt_powerkey(void);
/* sys.demo_enabled: LED demo and suppression of normal button actions. */
uint32_t syscon_target_demo_enabled(void);
/* sys.enable_5v_when_off: header supply policy, not processor power state. */
uint32_t syscon_target_keep_5v_when_off(void);
uint32_t syscon_target_powerkey_long_seconds(void);
uint32_t syscon_target_powerkey_extra_seconds(void);
uint32_t syscon_target_hwrevision_new(void);
void syscon_target_diagnostics_enable(uint32_t enabled);
void syscon_target_diagnostics_poll(void);
#endif
