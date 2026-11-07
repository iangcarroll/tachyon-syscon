#ifndef SYSCON_FAULT_CONTROL_TARGET_H
#define SYSCON_FAULT_CONTROL_TARGET_H
#include <stdint.h>
_Noreturn void syscon_target_assert(uint32_t file, uint32_t line, uint32_t expression);
void syscon_target_fault_stage_set(uint32_t stage);
uint32_t syscon_target_fault_stage_get(void);
uint32_t syscon_target_fault_stage_name(uint32_t stage);
uint32_t syscon_target_enable_mftick(void);
uint32_t syscon_target_cached_reason(void);
#endif
