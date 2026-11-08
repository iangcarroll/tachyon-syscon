#include "pwm_target.h"
#include "pwm_state.h"
#include "hal_helpers.h"
#include "mspm0_core_target.h"
#include "runtime_memory.h"
#define U8(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))
static void pwm_assert(uint32_t original_line, const char *expression)
{
    syscon_target_assert((uint32_t)(uintptr_t)"hal_pwm.cpp", original_line,
                         (uint32_t)(uintptr_t)expression);
}
/* Timer register offsets and update masks are hardware contracts. */
enum {
    TIMER_CONTROL = 0x1804,
    TIMER_PERIOD = 0x1808,
    COMPARE_BASE = 0x1810,
    CAPTURE_CONTROL_BASE = 0x1830,
    CAPTURE_FILTER_BASE = 0x1850,
    ACTION_BASE = 0x1870,
    OUTPUT_CONTROL_BASE = 0x1880,
};

void syscon_target_pwm_clock(uint32_t base, uint32_t config)
{
    uint32_t source = U8(config);
    U32(base + 0x1008u) = source;
    uint32_t divider = U8(config + 1u);
    U32(base + 0x1000u) = divider;
    uint32_t prescaler = U8(config + 2u);
    U32(base + 0x110cu) = prescaler;
}

void syscon_target_pwm_compare(uint32_t base, uint32_t value, uint32_t index)
{
    U32(base + COMPARE_BASE + index * 4u) = value;
}

void syscon_target_pwm_capture(uint32_t base, uint32_t a, uint32_t b, uint32_t index)
{
    uint32_t address = base + CAPTURE_CONTROL_BASE + index * 4u;
    uint32_t old = U32(address);
    U32(address) = old ^ ((old ^ (a | b)) & 0x27777u);
}

void syscon_target_pwm_action(uint32_t base, uint32_t value, uint32_t index)
{
    uint32_t address = base + ACTION_BASE + index * 4u;
    uint32_t old = U32(address);
    U32(address) = old ^ ((old ^ value) & 0xffc1b6dbu);
}

void syscon_target_pwm_output(uint32_t base, uint32_t a, uint32_t b, uint32_t index)
{
    uint32_t address = base + OUTPUT_CONTROL_BASE + index * 4u;
    uint32_t old = U32(address);
    U32(address) = old ^ ((old ^ (a | b)) & 0x8fu);
}

uint64_t syscon_target_pwm_configure(uint32_t base, uint32_t config)
{
    if (U8(config + 5u)) {
        uint32_t mode = U8(config + 4u);
        uint32_t action = mode == 0 ? 0x88u : mode == 0x20u ? 0x401u : 0x280u;
        syscon_target_pwm_action(base, action, 2);
        syscon_target_pwm_action(base, action, 3);
        syscon_target_pwm_capture(base, 0, 0, 2);
        syscon_target_pwm_capture(base, 0, 0, 3);
        U32(base + CAPTURE_FILTER_BASE + 8u) = 0;
        U32(base + CAPTURE_FILTER_BASE + 12u) = 0;
        syscon_target_pwm_output(base, 0, 0, 2);
        syscon_target_pwm_output(base, 0, 0, 3);
    }
    /* Reread mode after optional-channel writes: config may alias registers. */
    uint32_t control = U8(config + 6u);
    uint32_t mode = U8(config + 4u);
    uint32_t period = U32(config);
    uint32_t action;
    if (mode == 0 || mode == 0x20u) {
        U32(base + TIMER_PERIOD) = period - 1u;
        action = mode ? 0x401u : 0x88u;
    } else {
        U32(base + TIMER_PERIOD) = period >> 1;
        action = 0x280u;
    }
    syscon_target_pwm_action(base, action, 0);
    syscon_target_pwm_action(base, action, 1);
    if (mode == 0x20u) {
        uint32_t old = U32(base + TIMER_CONTROL);
        U32(base + TIMER_CONTROL) = old ^ ((old ^ 0x20000000u) & 0x30000000u);
    }
    syscon_target_pwm_capture(base, 0, 0, 0);
    syscon_target_pwm_capture(base, 0, 0, 1);
    U32(base + CAPTURE_FILTER_BASE) = 0;
    U32(base + CAPTURE_FILTER_BASE + 4u) = 0;
    syscon_target_pwm_output(base, 0, 0, 0);
    syscon_target_pwm_output(base, 0, 0, 1);
    uint32_t old = U32(base + TIMER_CONTROL);
    U32(base + TIMER_CONTROL) = old ^ ((old ^ (control | mode | 2u)) & 0x3000ffbfu);
    return base | ((uint64_t)control << 32);
}

uint32_t syscon_target_pwm_init(uint32_t pin)
{
    volatile syscon_pwm_channel_t *pwm =
        (volatile syscon_pwm_channel_t *)(uintptr_t)syscon_hal_pwm_lookup(pin);
    uint32_t gpio = syscon_target_gpio_lookup(pin);
    /* Both lookups precede validation, preserving the original failure order. */
    if (!pwm)
        pwm_assert(13, "pwm != nullptr");
    if (!gpio)
        pwm_assert(14, "gpio != nullptr");
    uint32_t port = U32(gpio);
    U32(port + 0x800u) = 0x26000001u;
    uint32_t function = pwm->mux_function;
    uint32_t mux = U8(gpio + 5u);
    U32(0x40428004u + mux * 4u) = function | 0x80u;
    uint32_t base = pwm->peripheral;
    uint32_t enabled = U32(base + 0x800u);
    if (!(enabled & 1u)) {
        U32(base + 0x804u) = 0xb1000003u;
        U32(base + 0x800u) = 0x26000001u;
        uint32_t clock = 2;
        syscon_target_pwm_clock(base, (uint32_t)(uintptr_t)&clock);
        uint32_t config[2] = {256, 0};
        base = pwm->peripheral;
        syscon_target_pwm_configure(base, (uint32_t)(uintptr_t)config);
        base = pwm->peripheral;
        U32(base + 0x1108u) = 1;
        U32(base + 0x1100u) = 3;
    }
    return 0;
}

uint32_t syscon_target_pwm_write(uint32_t pin, uint32_t value)
{
    volatile syscon_pwm_channel_t *pwm =
        (volatile syscon_pwm_channel_t *)(uintptr_t)syscon_hal_pwm_lookup(pin);
    if (!pwm)
        pwm_assert(43, "pwm != nullptr");
    uint32_t base = pwm->peripheral;
    uint32_t old = U32(base + TIMER_CONTROL);
    U32(base + TIMER_CONTROL) = old & ~1u;
    uint32_t index = pwm->compare_index;
    syscon_target_pwm_compare(base, value, index);
    base = pwm->peripheral;
    old = U32(base + TIMER_CONTROL);
    U32(base + TIMER_CONTROL) = old | 1u;
    return 0;
}
