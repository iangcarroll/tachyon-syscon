/* Power-button debounce, press classification and modem-key forwarding. */
#include "power_key_target.h"
#include "power_key_state.h"
#include "power_key_text.h"
#include "scheduling_target.h"
#include "mspm0_core_target.h"
#include "diagnostics_target.h"
#include "runtime_memory.h"

volatile syscon_powerkey_range_t syscon_powerkey_ranges[3]
    __attribute__((section(".data.syscon_powerkey_ranges"))) = {
        {50, 3000, 0, {0}},
        {3000, 8000, 2, {0}},
        {8000, UINT32_MAX, 4, {0}},
};
volatile syscon_powerkey_control_t syscon_powerkey_control
    __attribute__((section(".data.syscon_powerkey_control"))) = {1, 255};
volatile syscon_powerkey_runtime_t syscon_powerkey_runtime
    __attribute__((section(".bss.syscon_powerkey_runtime")));

#define CONTROL syscon_powerkey_control
#define STATE syscon_powerkey_runtime
#define ADDRESS(fn) ((uint32_t)(uintptr_t)(fn))
enum {
    BUTTON_PIN = 0,
    POLL_MS = 10,
    RELEASE_DEBOUNCE_MS = 200,
    FORCE_RELEASE_MS = 6000,
    EXTRA_PRESS_MS = 5000,
    NO_PRESS = 255,
};

static void attach(void)
{
    (void)syscon_target_gpio_attach(BUTTON_PIN, 0, ADDRESS(syscon_target_powerkey_edge), 0);
}

int syscon_target_powerkey_edge(uint32_t pin)
{
    (void)syscon_target_gpio_read(pin);
    syscon_target_timer_unregister(ADDRESS(syscon_target_powerkey_poll));
    STATE.pin = (uint16_t)pin;
    (void)syscon_target_gpio_detach(BUTTON_PIN);
    return syscon_target_timer_register(POLL_MS, 1, ADDRESS(syscon_target_powerkey_debounce), 0);
}

void syscon_target_powerkey_poll(uint32_t ignored)
{
    (void)ignored;
    uint8_t old_event = CONTROL.event;
    if (!syscon_target_gpio_read(BUTTON_PIN)) {
        STATE.pressed_ms = STATE.pressed_ms + POLL_MS;
        STATE.released_ms = 0;
        if (!CONTROL.mode && !STATE.forced && STATE.pressed_ms >= FORCE_RELEASE_MS) {
            syscon_target_modem_key_release();
            STATE.forced = 1;
        }
    } else {
        STATE.release_pending = 1;
        STATE.released_ms = STATE.released_ms + POLL_MS;
        STATE.pressed_ms = 0;
    }

    for (unsigned i = 0; i < 3; ++i) {
        volatile syscon_powerkey_range_t *range = &syscon_powerkey_ranges[i];
        uint32_t pressed = STATE.pressed_ms;
        uint32_t start = range->start_ms;
        if (start > pressed)
            continue;
        /* Keep the second volatile read: interrupt/callback-visible state is
         * not a cached snapshot of the first comparison. */
        pressed = STATE.pressed_ms;
        uint32_t end = range->end_ms;
        if (end > pressed) {
            CONTROL.event = range->event;
            break;
        }
    }

    uint8_t finished = STATE.release_pending;
    if (finished) {
        if (STATE.released_ms <= RELEASE_DEBOUNCE_MS)
            finished = 0;
        else
            CONTROL.event = CONTROL.event + 1;
    }
    if (CONTROL.event != old_event) {
        uint32_t callback = STATE.callback;
        if (callback) {
            uint8_t event = CONTROL.event;
            uint32_t context = STATE.context;
            ((void (*)(uint32_t, uint32_t))(uintptr_t)callback)(event, context);
        }
    }
    /* The callback may change state. Completion deliberately uses the decision
     * made before that callback, matching the original cleanup behavior. */
    if (finished) {
        STATE.release_pending = 0;
        CONTROL.event = NO_PRESS;
        syscon_target_timer_unregister(ADDRESS(syscon_target_powerkey_poll));
        attach();
    }
}

void syscon_target_powerkey_debounce(uint32_t ignored)
{
    (void)ignored;
    uint32_t high = syscon_target_gpio_read(STATE.pin);
    uint32_t rearm;
    if (!CONTROL.mode) {
        if (high)
            syscon_target_modem_key_release();
        else
            syscon_target_modem_key_assert();
    }
    if (high) {
        rearm = 1;
        if (CONTROL.event == NO_PRESS) {
            attach();
            return;
        }
    } else {
        rearm = CONTROL.mode == 0;
        if (CONTROL.event == NO_PRESS) {
            STATE.release_pending = 0;
            STATE.pressed_ms = 0;
            STATE.released_ms = 0;
            STATE.forced = 0;
            uint32_t seconds = syscon_target_modem_off() ? syscon_target_powerkey_long_seconds()
                                                         : syscon_target_powerkey_extra_seconds();
            /* Unsigned arithmetic, including wrap, matches the stored timer
             * configuration. Do not silently clamp the caller's value. */
            uint32_t ms = seconds * 1000;
            uint32_t extended = ms + EXTRA_PRESS_MS;
            syscon_powerkey_ranges[0].end_ms = ms;
            syscon_powerkey_ranges[1].start_ms = ms;
            syscon_powerkey_ranges[1].end_ms = extended;
            syscon_powerkey_ranges[2].start_ms = extended;
        }
    }
    (void)syscon_target_timer_register(POLL_MS, 0, ADDRESS(syscon_target_powerkey_poll), 0);
    if (rearm)
        attach();
}

int syscon_target_powerkey_callback(uint32_t function, uint32_t context)
{
    STATE.callback = function;
    STATE.context = context;
    return 0;
}

void syscon_target_powerkey_mode(uint32_t mode)
{
    CONTROL.mode = (uint8_t)mode;
    syscon_target_logger(3, SYSCON_POWERKEY_LOG_TAG, SYSCON_POWERKEY_MODE_CHANGED,
                         mode ? SYSCON_POWERKEY_DETECT : SYSCON_POWERKEY_PASSTHRU);
    syscon_target_timer_unregister(ADDRESS(syscon_target_powerkey_poll));
    attach();
    CONTROL.event = NO_PRESS;
}

int syscon_target_powerkey_init(uint32_t mode)
{
    uint8_t configuration[12];
    syscon_rt_memset(configuration, 0, sizeof(configuration));
    configuration[5] = 1;
    (void)syscon_target_gpio_config(BUTTON_PIN, (uint32_t)(uintptr_t)configuration);
    syscon_target_powerkey_mode(mode);
    syscon_target_timer_init();
    return 0;
}
