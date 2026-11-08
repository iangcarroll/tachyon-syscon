/* RGB animation and temporary presets, with linker-allocated state and data. */
#include "rgb_target.h"
#include "rgb_state.h"
#include "rgb_data.h"
#include "runtime_memory.h"
#include "scheduling_target.h"
#include "pwm_target.h"
#include <stddef.h>
#include <stdint.h>

#define BYTE(address) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(address))
#define STATE syscon_rgb_runtime
#define COUNT(array) (sizeof(array) / sizeof((array)[0]))
enum { TICK_MS = 20, PWM_RED = 3, PWM_GREEN = 2, PWM_BLUE = 1 };

volatile syscon_rgb_runtime_t syscon_rgb_runtime
    __attribute__((section(".bss.syscon_rgb_runtime")));

static float decode(uint32_t bits)
{
    union {
        uint32_t u;
        float f;
    } value = {.u = bits};
    return value.f;
}

static uint32_t encode(float value)
{
    union {
        float f;
        uint32_t u;
    } bits = {.f = value};
    return bits.u;
}

extern uint32_t syscon_rt_f2u(uint32_t bits);

uint32_t syscon_target_rgb_scale(uint32_t channel)
{
    /* Use the defined bit-level helper, including NaNs and out-of-range input. */
    uint8_t level = (uint8_t)syscon_rt_f2u(STATE.level_bits);
    uint8_t value = (uint8_t)((channel * (uint32_t)level) / 100u);
    if (!STATE.active_high)
        value = (uint8_t)~value;
    return value;
}

void syscon_target_rgb_flush(void)
{
    /* Do not snapshot all channels: a PWM callback may change a later one. */
    uint32_t value = syscon_target_rgb_scale(STATE.red);
    syscon_target_pwm_write(PWM_RED, value);
    value = syscon_target_rgb_scale(STATE.green);
    syscon_target_pwm_write(PWM_GREEN, value);
    value = syscon_target_rgb_scale(STATE.blue);
    syscon_target_pwm_write(PWM_BLUE, value);
}

int syscon_target_rgb_init(uint32_t active_high)
{
    syscon_target_pwm_init(PWM_RED);
    syscon_target_pwm_init(PWM_GREEN);
    syscon_target_pwm_init(PWM_BLUE);
    syscon_rt_memset((void *)&STATE, 0, offsetof(syscon_rgb_runtime_t, palette_index));
    STATE.active_high = (uint8_t)active_high;
    int result =
        syscon_target_timer_register(TICK_MS, 0, (uint32_t)(uintptr_t)syscon_target_rgb_tick, 0);
    if (result < 0)
        syscon_target_logger(1, SYSCON_RGB_LOG_TAG, SYSCON_RGB_TIMER_FAILED, result);
    syscon_target_timer_init();
    return 0;
}

int syscon_target_rgb_brightness(uint32_t brightness, uint32_t flush)
{
    if (brightness > 100)
        brightness = 100;
    STATE.brightness = (uint8_t)brightness;
    STATE.level_bits = encode((float)brightness);
    if (flush)
        syscon_target_rgb_flush();
    return 0;
}

int syscon_target_rgb_pattern(uint32_t pattern, uint32_t flush)
{
    /* Compare the full caller word before truncating storage to one byte. */
    if (STATE.pattern != pattern) {
        STATE.pattern = (uint8_t)pattern;
        if (pattern == SYSCON_RGB_BREATHING)
            STATE.increasing = 0;
        else if (pattern == SYSCON_RGB_BLINKING)
            STATE.interval_ms = 500;
        else if (pattern == SYSCON_RGB_BLINKING_RAPIDLY)
            STATE.interval_ms = 100;
        STATE.ticks = 0;
    }
    if (flush)
        syscon_target_rgb_flush();
    return 0;
}

int syscon_target_rgb_configure(uint32_t config)
{
    if (!config)
        return -1;
    /* Preserve byte-read/write order when the input aliases live RGB state. */
    uint32_t green = BYTE(config + 1);
    uint32_t blue = BYTE(config + 2);
    uint32_t red = BYTE(config);
    STATE.green = (uint8_t)green;
    STATE.red = (uint8_t)red;
    STATE.blue = (uint8_t)blue;
    syscon_target_rgb_brightness(BYTE(config + 3), 0);
    return syscon_target_rgb_pattern(BYTE(config + 4), 1);
}

int syscon_target_rgb_preset(uint32_t preset, uint32_t duration)
{
    if (preset >= COUNT(syscon_rgb_presets))
        return -1;
    uint32_t previous = STATE.preset;
    STATE.preset = (uint8_t)preset;
    STATE.previous_preset = (uint8_t)previous;
    STATE.duration_ticks = duration / TICK_MS;
    return syscon_target_rgb_configure((uint32_t)(uintptr_t)&syscon_rgb_presets[preset]);
}

uint64_t syscon_target_rgb_tick(uint32_t arg, uint32_t seed)
{
    uint32_t duration = STATE.duration_ticks;
    if (duration) {
        --duration;
        STATE.duration_ticks = duration;
        if (!duration)
            syscon_target_rgb_preset(STATE.previous_preset, 0);
    }
    uint32_t pattern = STATE.pattern;
    if (pattern == SYSCON_RGB_BREATHING) {
        uint32_t brightness = STATE.brightness;
        float target = (float)(int32_t)brightness;
        seed = encode(target);
        float step = target / 100.0f;
        uint32_t increasing = STATE.increasing;
        float level = decode(STATE.level_bits);
        if (!increasing) {
            if (level <= step) {
                STATE.level_bits = 0;
                STATE.increasing = (uint8_t)pattern;
            } else {
                STATE.level_bits = encode(decode(STATE.level_bits) - step);
            }
        } else {
            STATE.level_bits = encode(level + step);
            if (target <= decode(STATE.level_bits)) {
                STATE.level_bits = encode((float)brightness);
                STATE.increasing = 0;
            }
        }
    } else if (pattern - SYSCON_RGB_BLINKING < 2u) {
        STATE.ticks = (uint8_t)(STATE.ticks + 1u);
        uint32_t elapsed = STATE.ticks * TICK_MS;
        uint32_t interval = STATE.interval_ms;
        if (elapsed < interval)
            return ((uint64_t)seed << 32) | arg;
        STATE.ticks = 0;
        if (decode(STATE.level_bits) == 0.0f)
            STATE.level_bits = encode((float)STATE.brightness);
        else
            STATE.level_bits = 0;
    } else if (pattern == SYSCON_RGB_RAINBOW) {
        STATE.ticks = (uint8_t)(STATE.ticks + 1u);
        if (STATE.ticks < 3)
            return ((uint64_t)seed << 32) | arg;
        STATE.ticks = 0;
        uint32_t next = (uint8_t)(STATE.palette_index + 1u);
        STATE.palette_index = (uint8_t)(next < COUNT(syscon_rgb_palette) ? next : 0);
        const syscon_rgb_color_t *color = &syscon_rgb_palette[STATE.palette_index];
        uint32_t green = color->green;
        uint32_t red = color->red;
        uint32_t blue = color->blue;
        STATE.red = (uint8_t)red;
        STATE.green = (uint8_t)green;
        STATE.blue = (uint8_t)blue;
    } else {
        return ((uint64_t)seed << 32) | arg;
    }
    syscon_target_rgb_flush();
    return ((uint64_t)seed << 32) | arg;
}

uint32_t syscon_target_rgb_state(void)
{
    return STATE.preset;
}

uint32_t syscon_target_rgb_get_config(uint32_t out)
{
    if (!out)
        return 0;
    BYTE(out) = STATE.preset;
    BYTE(out + 1) = STATE.red;
    BYTE(out + 2) = STATE.green;
    BYTE(out + 3) = STATE.blue;
    BYTE(out + 4) = STATE.brightness;
    BYTE(out + 5) = STATE.pattern;
    return 1;
}

uint32_t syscon_target_rgb_state_name(uint32_t state)
{
    return (uint32_t)(uintptr_t)(state < COUNT(syscon_rgb_preset_names)
                                     ? syscon_rgb_preset_names[state]
                                     : SYSCON_RGB_UNKNOWN);
}

uint32_t syscon_target_rgb_pattern_name(uint32_t pattern)
{
    return (uint32_t)(uintptr_t)(pattern < COUNT(syscon_rgb_pattern_names)
                                     ? syscon_rgb_pattern_names[pattern]
                                     : SYSCON_RGB_UNKNOWN);
}

void syscon_target_rgb_key_feedback(void)
{
    syscon_target_rgb_preset(SYSCON_RGB_TRANSIENT, 2 * TICK_MS);
}
