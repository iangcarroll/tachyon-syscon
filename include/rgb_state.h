#ifndef SYSCON_RGB_STATE_H
#define SYSCON_RGB_STATE_H
#include <stdint.h>

enum syscon_rgb_pattern {
    SYSCON_RGB_OFF, SYSCON_RGB_BREATHING, SYSCON_RGB_BLINKING,
    SYSCON_RGB_BLINKING_RAPIDLY, SYSCON_RGB_SOLID, SYSCON_RGB_RAINBOW,
};
enum syscon_rgb_preset {
    SYSCON_RGB_STATE_OFF, SYSCON_RGB_FASTBOOT, SYSCON_RGB_EDL, SYSCON_RGB_FACTORY,
    SYSCON_RGB_BOOTING, SYSCON_RGB_RUNNING, SYSCON_RGB_WIFI, SYSCON_RGB_LTE,
    SYSCON_RGB_SIGNAL, SYSCON_RGB_TRANSIENT,
};
typedef struct {
    uint8_t pattern, red, green, blue, brightness;
    uint8_t reserved0[3];
    /* IEEE-754 bits, not a C integer conversion of the brightness level. */
    uint32_t level_bits;
    uint8_t increasing, ticks;
    uint16_t interval_ms;
    uint8_t active_high;
    uint8_t reserved1[3];
    /* Reinitialization preserves this tail, matching the original lifecycle. */
    uint8_t palette_index, preset, previous_preset, reserved2;
    uint32_t duration_ticks;
} syscon_rgb_runtime_t;
extern volatile syscon_rgb_runtime_t syscon_rgb_runtime;
#endif
