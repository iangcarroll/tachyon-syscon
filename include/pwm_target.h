#ifndef SYSCON_PWM_TARGET_H
#define SYSCON_PWM_TARGET_H
#include <stdint.h>
uint32_t syscon_target_pwm_init(uint32_t pin);
uint32_t syscon_target_pwm_write(uint32_t pin,uint32_t value);
void syscon_target_pwm_clock(uint32_t base,uint32_t config);
void syscon_target_pwm_compare(uint32_t base,uint32_t value,uint32_t index);
void syscon_target_pwm_capture(uint32_t base,uint32_t a,uint32_t b,uint32_t index);
void syscon_target_pwm_action(uint32_t base,uint32_t value,uint32_t index);
void syscon_target_pwm_output(uint32_t base,uint32_t a,uint32_t b,uint32_t index);
uint64_t syscon_target_pwm_configure(uint32_t base,uint32_t config);
#endif
