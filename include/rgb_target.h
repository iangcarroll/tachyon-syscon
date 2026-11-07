#ifndef SYSCON_RGB_TARGET_H
#define SYSCON_RGB_TARGET_H
#include <stdint.h>
uint32_t syscon_target_rgb_scale(uint32_t);
void syscon_target_rgb_flush(void);
int syscon_target_rgb_init(uint32_t);
int syscon_target_rgb_brightness(uint32_t,uint32_t);
int syscon_target_rgb_pattern(uint32_t,uint32_t);
int syscon_target_rgb_configure(uint32_t);
int syscon_target_rgb_preset(uint32_t,uint32_t);
uint64_t syscon_target_rgb_tick(uint32_t,uint32_t);
uint32_t syscon_target_rgb_state(void);
uint32_t syscon_target_rgb_get_config(uint32_t);
uint32_t syscon_target_rgb_state_name(uint32_t);
uint32_t syscon_target_rgb_pattern_name(uint32_t);
void syscon_target_rgb_key_feedback(void);
#endif
