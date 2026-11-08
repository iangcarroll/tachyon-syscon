#include "power_state.h"
/* Power report, startup routing, minimum voltage and shutdown-reason expiry. */
#include "power_policy_target.h"
#include "adc_target.h"
#include "scheduling_target.h"
#include "ioexpander_target.h"
#include "power_manager_target.h"
#include "logger_target.h"
#include <stdint.h>

static uint64_t shutdown_started(void)
{
    uint32_t low = syscon_shutdown_state.started_low, high = syscon_shutdown_state.started_high;
    return low | ((uint64_t)high << 32);
}
static void shutdown_start(uint64_t value)
{
    syscon_shutdown_state.started_low = (uint32_t)value;
    syscon_shutdown_state.started_high = (uint32_t)(value >> 32);
}
void syscon_target_power_report(uint32_t printer)
{
    void (*out)(const char *, ...) = (void (*)(const char *, ...))(uintptr_t)printer;
    int32_t vph = (int32_t)syscon_target_power_measure(12);
    uint32_t header = syscon_target_power_measure(13), battery = syscon_target_power_measure(14);
    int32_t usb = (int32_t)syscon_target_power_measure(16),
            v18 = (int32_t)syscon_target_power_measure(15);
    uint32_t vbatt = syscon_target_power_battery_route(), batt = syscon_target_retained_battery();
    uint32_t vbus = syscon_target_power_vbus_route(), hdr = syscon_target_power_header_route();
    out("--- Power Status ---");
    out("   Battery     : %s (%dmV)", syscon_power_name(syscon_power_names.battery, batt), battery);
    uint32_t id = syscon_target_power_battery_id();
    out("   Battery id  : %s", id == 1 ? "fake_10k" : "battery");
    uint32_t ntc = syscon_target_power_ntc();
    out("   NTC         : %s", syscon_power_name(syscon_power_names.ntc, ntc));
    out("   USB         : %s (%dmV)", usb > 4499 ? "attached" : "detached", usb);
    uint32_t removed = syscon_target_pin_read(32);
    out("   D+/D-       : %s", removed ? "off connector" : "on connector");
    out("   5V header   : %s (%dmV)", syscon_power_name(syscon_power_names.header, hdr), header);
    uint32_t boost = syscon_target_power_boost();
    out("   5V booster  : %s", boost ? "enabled" : "disabled");
    out("   SG560D vbus : %s", syscon_power_name(syscon_power_names.vbus_route, vbus));
    out("   SG560D vbatt: %s", syscon_power_name(syscon_power_names.battery_route, vbatt));
    out("   SG560D 1v8      : %s (%dmV)", v18 > 1700 ? "on" : "off", v18);
    out("   SG560D vph      : %s (%dmV)", vph > 3000 ? "on" : "off", vph);
    out("--------------------");
}
int32_t syscon_target_power_policy_init(uint32_t cold)
{
    uint8_t config[7] = {0, 0, 7, 0, 8, 7, 12};
    syscon_target_adc_init(12, (uint32_t)(uintptr_t)config);
    syscon_target_adc_init(13, (uint32_t)(uintptr_t)config);
    syscon_target_adc_init(14, (uint32_t)(uintptr_t)config);
    syscon_target_adc_init(15, (uint32_t)(uintptr_t)config);
    syscon_target_adc_init(16, (uint32_t)(uintptr_t)config);
    syscon_target_adc_init(23, (uint32_t)(uintptr_t)config);
    if (!cold)
        syscon_target_power_report((uint32_t)(uintptr_t)syscon_target_mfg_logger);
    else {
        uint8_t output[3] = {1, 0, 1};
        static const uint8_t low[] = {8, 9, 10, 12, 13, 0, 15, 7, 1};
        static const uint8_t high[] = {2, 3, 11};
        for (unsigned i = 0; i < sizeof(low); ++i)
            syscon_target_ioexpander_configure(low[i], (const syscon_io_config *)output);
        output[1] = 1;
        for (unsigned i = 0; i < sizeof(high); ++i)
            syscon_target_ioexpander_configure(high[i], (const syscon_io_config *)output);
    }
    return 0;
}
void syscon_target_power_minimum_update(void)
{
    int32_t measured = (int32_t)syscon_target_power_measure(12);
    if (measured < (int32_t)syscon_minimum_vph_mv)
        syscon_minimum_vph_mv = (uint32_t)measured;
}
void syscon_target_power_minimum_reset(void)
{
    syscon_minimum_vph_mv = INT32_MAX;
}
uint32_t syscon_target_power_minimum(void)
{
    uint32_t value = syscon_minimum_vph_mv;
    return value == INT32_MAX ? UINT32_MAX : value;
}
void syscon_target_shutdown_set(uint32_t reason)
{
    syscon_target_logger(3, "PMGR", "Shutdown reason set: %s",
                         syscon_power_name(syscon_power_names.shutdown, reason));
    syscon_shutdown_reason = (uint8_t)reason;
    syscon_shutdown_state.stale = 0;
    uint64_t now = reason ? syscon_target_now() : 0;
    shutdown_start(now);
}
uint32_t syscon_target_shutdown_reason(void)
{
    return syscon_shutdown_reason;
}
uint64_t syscon_target_shutdown_elapsed(void)
{
    if (!shutdown_started())
        return 0;
    uint64_t now = syscon_target_now(), start = shutdown_started();
    return now > start ? now - start : 0;
}
uint32_t syscon_target_shutdown_stale(void)
{
    return syscon_shutdown_state.stale;
}
uint32_t syscon_target_shutdown_active(void)
{
    return syscon_shutdown_state.stale ? 0 : syscon_shutdown_reason;
}
void syscon_target_shutdown_poll(void)
{
    uint32_t reason = syscon_shutdown_reason;
    uint64_t start = shutdown_started(), now = syscon_target_now();
    if (!syscon_shutdown_state.stale && reason && start && now - start > 299999) {
        reason = syscon_shutdown_reason;
        syscon_target_logger(2, "PMGR",
                             "Shutdown reason %s timed out after %d minutes - marking as stale",
                             syscon_power_name(syscon_power_names.shutdown, reason), 5);
        syscon_shutdown_state.stale = 1;
    }
}
