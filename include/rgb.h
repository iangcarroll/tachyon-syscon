#ifndef SYSCON_RGB_H
#define SYSCON_RGB_H
#include <stddef.h>
#include <stdint.h>

typedef struct {
    uint8_t pattern, red, green, blue, brightness, padding0[3];
    float level;
    uint8_t increasing, ticks;
    uint16_t interval;
    uint8_t active_high, padding1[3];
    uint8_t palette_index, state, previous_state, padding2;
    uint32_t duration_ticks;
} syscon_rgb_state;
_Static_assert(sizeof(syscon_rgb_state)==28,"RGB RAM span");
_Static_assert(offsetof(syscon_rgb_state,level)==8,"RGB float offset");
_Static_assert(offsetof(syscon_rgb_state,duration_ticks)==24,"RGB timeout offset");
typedef struct {
    void *context;
    void (*pwm_init)(void *, unsigned);
    void (*pwm_write)(void *, unsigned, unsigned);
    int (*timer_register)(void *, unsigned, unsigned, uint32_t, uint32_t);
    void (*timer_init)(void *);
    void (*timer_error)(void *);
} syscon_rgb_io;

uint8_t syscon_rgb_scale(const syscon_rgb_state *, unsigned channel);
void syscon_rgb_flush(const syscon_rgb_state *, const syscon_rgb_io *);
int syscon_rgb_init(syscon_rgb_state *, const syscon_rgb_io *, unsigned active_high);
int syscon_rgb_brightness(syscon_rgb_state *, const syscon_rgb_io *, unsigned, int flush);
int syscon_rgb_pattern(syscon_rgb_state *, const syscon_rgb_io *, unsigned, int flush);
int syscon_rgb_configure(syscon_rgb_state *, const syscon_rgb_io *, const uint8_t config[5]);
int syscon_rgb_set_state(syscon_rgb_state *, const syscon_rgb_io *, unsigned, uint32_t duration_ms);
void syscon_rgb_tick(syscon_rgb_state *, const syscon_rgb_io *);
unsigned syscon_rgb_get_state(const syscon_rgb_state *);
int syscon_rgb_get_config(const syscon_rgb_state *, uint8_t config[6]);
const char *syscon_rgb_state_name(unsigned);
const char *syscon_rgb_pattern_name(unsigned);
void syscon_rgb_transient(syscon_rgb_state *, const syscon_rgb_io *);
#endif
