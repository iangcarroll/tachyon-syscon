#ifndef SYSCON_PWM_STATE_H
#define SYSCON_PWM_STATE_H
#include <stdint.h>

typedef struct {
    uint8_t pin, mux_function;
    uint8_t reserved[2];
    uint32_t peripheral;
    uint8_t compare_index;
    uint8_t trailing_reserved[3];
} syscon_pwm_channel_t;
extern volatile syscon_pwm_channel_t syscon_pwm_channels[3];
#endif
