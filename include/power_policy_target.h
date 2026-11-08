#ifndef SYSCON_POWER_POLICY_TARGET_H
#define SYSCON_POWER_POLICY_TARGET_H
#include <stdint.h>
void syscon_target_power_report(uint32_t printer);
int32_t syscon_target_power_policy_init(uint32_t cold);
void syscon_target_power_minimum_update(void);
void syscon_target_power_minimum_reset(void);
uint32_t syscon_target_power_minimum(void);
void syscon_target_shutdown_set(uint32_t reason);
uint32_t syscon_target_shutdown_reason(void);
uint64_t syscon_target_shutdown_elapsed(void);
uint32_t syscon_target_shutdown_stale(void);
/* Returns the reason byte while fresh, otherwise 0; not a boolean. */
uint32_t syscon_target_shutdown_reason_if_fresh(void);
void syscon_target_shutdown_poll(void);
#endif
