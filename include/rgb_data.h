#ifndef SYSCON_RGB_DATA_H
#define SYSCON_RGB_DATA_H
#include "rgb_state.h"

typedef struct { uint8_t red, green, blue, brightness, pattern; } syscon_rgb_setting_t;
typedef struct { uint8_t red, green, blue; } syscon_rgb_color_t;

/* The OFF preset intentionally indicates the off state with dim red. */
static const syscon_rgb_setting_t syscon_rgb_presets[] = {
    [SYSCON_RGB_STATE_OFF] = {255,   0,   0,  20, SYSCON_RGB_SOLID},
    [SYSCON_RGB_FASTBOOT]  = {255,   0, 255,  30, SYSCON_RGB_BLINKING},
    [SYSCON_RGB_EDL]       = {180,  80,   0,  80, SYSCON_RGB_BLINKING},
    [SYSCON_RGB_FACTORY]   = {255, 255, 255,  30, SYSCON_RGB_BLINKING},
    [SYSCON_RGB_BOOTING]   = {  0, 255,   0, 100, SYSCON_RGB_BLINKING},
    [SYSCON_RGB_RUNNING]   = {  0, 255,   0, 100, SYSCON_RGB_BREATHING},
    [SYSCON_RGB_WIFI]      = {255,   0, 255, 100, SYSCON_RGB_BREATHING},
    [SYSCON_RGB_LTE]       = {  0, 255, 255, 100, SYSCON_RGB_BREATHING},
    [SYSCON_RGB_SIGNAL]    = {  0,   0,   0, 100, SYSCON_RGB_RAINBOW},
    [SYSCON_RGB_TRANSIENT] = {255, 255, 255,  50, SYSCON_RGB_SOLID},
};
static const syscon_rgb_color_t syscon_rgb_palette[] = {
    {255,   0,   0}, {255, 170,   0}, {170, 255,   0}, {  0, 255,  85},
    {  0, 255, 255}, {  0,  85, 255}, { 85,   0, 255}, {170,   0, 255},
    {255,   0, 170}, {255,   0,  85},
};
static const char *const syscon_rgb_preset_names[] = {
    "off", "fastboot", "edl", "fct", "booting", "running",
    "connected_wifi", "connected_lte", "signal", "transient",
};
static const char *const syscon_rgb_pattern_names[] = {
    "off", "breathing", "blinking", "blinking_rapidly", "solid", "rainbow",
};
#define SYSCON_RGB_UNKNOWN "unknown"
#define SYSCON_RGB_LOG_TAG "RGBB"
#define SYSCON_RGB_TIMER_FAILED "systick_register_callback(20, false, on_timer_expired, nullptr) failed: %d"
#endif
