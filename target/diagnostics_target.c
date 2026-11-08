/* Original target configuration accessors and diagnostic loop. */
#include "diagnostics_target.h"
#include "diagnostics_state.h"
#include "config_state.h"
#include "runtime_scan.h"
#include "scheduling_target.h"
#include "power_manager_target.h"
#include "mspm0_core_target.h"
#include "adc_target.h"
#include "sg560d_target.h"
#include "power_policy_target.h"
#include "logger_target.h"
#include <stdint.h>

uint32_t syscon_target_auto_boot(void)
{
    return syscon_config_state.flags[SYSCON_CONFIG_AUTO_BOOT];
}
uint32_t syscon_target_wakeup_enabled(void)
{
    return syscon_config_state.flags[SYSCON_CONFIG_WAKE_PIN];
}
uint32_t syscon_target_log_color(void)
{
    return syscon_config_state.flags[SYSCON_CONFIG_COLOR_DEBUG];
}
uint32_t syscon_target_alt_powerkey(void)
{
    return syscon_config_state.flags[SYSCON_CONFIG_FASTBOOT];
}
uint32_t syscon_target_factory_test(void)
{
    return syscon_config_state.flags[SYSCON_CONFIG_DEMO];
}
uint32_t syscon_target_modem_always_on(void)
{
    return syscon_config_state.flags[SYSCON_CONFIG_KEEP_5V];
}
static uint32_t packed_read(const volatile uint8_t *base)
{
    /* Preserve the original nonmonotonic byte read order at unaligned fields. */
    uint32_t second = base[1], first = base[0], third = base[2], fourth = base[3];
    return first | (second << 8) | (third << 16) | (fourth << 24);
}
uint32_t syscon_target_powerkey_long_seconds(void)
{
    return packed_read(syscon_config_state.edl_timer_le);
}
uint32_t syscon_target_powerkey_extra_seconds(void)
{
    return packed_read(syscon_config_state.shutdown_timer_le);
}
uint32_t syscon_target_hwrevision_new(void)
{
    uint32_t major, minor, patch = 0;
    int fields =
        syscon_rt_sscanf(syscon_config_state.hardware_revision, "%u.%u.%u", &major, &minor, &patch);
    return fields == 3 && major == 1 && minor > 1;
}
void syscon_target_diagnostics_enable(uint32_t enabled)
{
    syscon_diagnostics_enabled = (uint8_t)enabled;
}
static uint64_t loop_count(void)
{
    uint32_t low = syscon_diagnostics_state.loops_low, high = syscon_diagnostics_state.loops_high;
    return ((uint64_t)high << 32) | low;
}
static void set_loop_count(uint64_t value)
{
    syscon_diagnostics_state.loops_low = (uint32_t)value;
    syscon_diagnostics_state.loops_high = (uint32_t)(value >> 32);
}
void syscon_target_diagnostics_poll(void)
{
    set_loop_count(loop_count() + 1u);
    uint64_t now = syscon_target_now();
    uint32_t previous_check = syscon_diagnostics_state.last_check_ms;
    if (now - (uint64_t)previous_check <= 5000)
        return;
    uint32_t current = (uint32_t)syscon_target_now();
    uint32_t previous = syscon_diagnostics_state.last_rate_ms;
    syscon_diagnostics_state.last_rate_ms = current;
    uint64_t loops = loop_count();
    set_loop_count(0);
    syscon_diagnostics_state.last_check_ms = current;
    if (!syscon_diagnostics_enabled)
        return;
    uint32_t uptime = (uint32_t)(syscon_target_now() / 1000u);
    uint32_t vph = syscon_target_power_measure(12);
    uint32_t v5 = syscon_target_power_measure(13);
    uint32_t vbat = syscon_target_power_measure(14);
    uint32_t vusb = syscon_target_power_measure(16);
    uint32_t v1v8 = syscon_target_power_measure(15);
    uint32_t wake = syscon_target_gpio_read(17);
    int32_t temperature = (int32_t)syscon_target_adc_temperature();
    uint8_t text[12];
    if (temperature == INT32_MIN)
        syscon_target_snprintf(text, 12, "--");
    else {
        int32_t whole = temperature / 10;
        uint32_t magnitude = temperature < 0 ? 0u - (uint32_t)temperature : (uint32_t)temperature;
        uint32_t fraction = magnitude % 10;
        if (temperature < 0 && whole == 0)
            syscon_target_snprintf(text, 12, "-0.%dC", fraction);
        else
            syscon_target_snprintf(text, 12, "%d.%dC", whole, fraction);
    }
    uint32_t off = syscon_target_modem_off();
    uint32_t minimum = syscon_target_power_minimum();
    syscon_target_logger(3, "DIAG", "VPH:%dmV 5V:%dmV vbat:%dmV mdm1v8:%dmV vusb:%dmV vphmin:%dmV",
                         vph, v5, vbat, v1v8, vusb, minimum);
    uint32_t seconds = (current - previous) / 1000u;
    /* The original public __aeabi_uldivmod explicitly returns all ones on
     * nonzero/zero and zero on zero/zero. Do not express C division-by-zero. */
    uint64_t rate = seconds ? loops / seconds : (loops ? UINT64_MAX : 0);
    syscon_target_logger(3, "DIAG", "uptime:%ds 560dpwr:%d loops:%i/s wakeup:%s mcu:%s", uptime,
                         (uint32_t)(uint8_t)(off ^ 1u), (uint32_t)rate, wake ? "HIGH" : "LOW",
                         text);
}
