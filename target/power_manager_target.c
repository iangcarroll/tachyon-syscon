#include "power_state.h"
#include "power_manager_target.h"
#include "runtime_memory.h"
#include "scheduling_target.h"
#include "fault_control_target.h"
#include "adc_target.h"
extern uint32_t syscon_target_pin_read(uint32_t pin);
extern uint32_t syscon_target_pin_write(uint32_t pin, uint32_t value);
#define LOG(level, format, ...) syscon_target_logger(level, "PMGR", format, ##__VA_ARGS__)
static void power_assert(uint32_t line, const char *expression)
{
    syscon_target_assert((uint32_t)(uintptr_t)"power_manager.cpp", line,
                         (uint32_t)(uintptr_t)expression);
}
uint32_t syscon_target_power_measure(uint32_t pin)
{
    uint32_t sample = syscon_target_adc_millivolts((uint16_t)pin);
    if (!sample)
        sample = syscon_target_adc_millivolts((uint16_t)pin);
    uint32_t index;
    if (pin >= 12u && pin <= 16u)
        index = pin - 12u;
    else if (pin == 23u)
        index = 5;
    else
        return 0;
    static const uint8_t scale[] = {3, 3, 3, 2, 8, 1};
    return sample * scale[index];
}
static uint32_t selector(uint32_t first, uint32_t second, uint32_t line)
{
    uint32_t a = syscon_target_pin_read(first), b = syscon_target_pin_read(second);
    if (a == 0 && b == 1)
        return 2;
    if (a <= 1 && b == 0)
        return a;
    power_assert(line, "false");
    return 0;
}
uint32_t syscon_target_power_battery_route(void)
{
    return selector(33, 34, 0x131);
}
uint32_t syscon_target_power_vbus_route(void)
{
    return selector(35, 26, 0x17c);
}
uint32_t syscon_target_power_header_route(void)
{
    return selector(40, 25, 0x1a2);
}
uint32_t syscon_target_power_battery_id(void)
{
    return syscon_target_pin_read(38) != 0;
}
uint32_t syscon_target_power_ntc(void)
{
    return syscon_target_pin_read(36) != 0;
}
uint32_t syscon_target_power_boost(void)
{
    return syscon_target_pin_read(37) != 0;
}
uint32_t syscon_target_power_battery_id_set(uint32_t fake_id)
{
    LOG(3, "Set BAT ID: %s", fake_id ? "FAKE_FOR_DCDC" : "BATTERY");
    return syscon_target_pin_write(38, fake_id != 0);
}
uint32_t syscon_target_power_ntc_set(uint32_t source)
{
    const char *name = syscon_power_name(syscon_power_names.ntc, source);
    LOG(3, "Set NTC source: %s", name);
    return syscon_target_pin_write(36, source != 0);
}
uint32_t syscon_target_power_boost_set(uint32_t enabled)
{
    return syscon_target_pin_write(37, enabled);
}
uint32_t syscon_target_power_battery_sense_set(uint32_t disabled)
{
    return syscon_target_pin_write(27, disabled != 0);
}
uint64_t syscon_target_power_battery_route_set(uint32_t route)
{
    uint32_t old = syscon_target_power_battery_route();
    if (old == route) {
        const char *name = syscon_power_name(syscon_power_names.battery_route, old);
        LOG(3, "Power path not changed: %s", name);
        return (uint64_t)route << 32;
    }
    if (old) {
        syscon_target_pin_write(33, 0);
        syscon_target_pin_write(34, 0);
    }
    if (route == 1) {
        syscon_target_power_ntc_set(0);
        syscon_target_power_battery_id_set(0);
        syscon_target_pin_write(33, 1);
    } else if (route == 2) {
        syscon_target_power_ntc_set(1);
        syscon_target_power_battery_id_set(1);
        syscon_target_pin_write(34, 1);
    } else
        syscon_target_power_ntc_set(1);
    const char *next_name = syscon_power_name(syscon_power_names.battery_route, route);
    const char *previous_name = syscon_power_name(syscon_power_names.battery_route, old);
    LOG(3, "Power path: %s -> %s", previous_name, next_name);
    return (uint64_t)(uintptr_t)next_name << 32;
}
uint64_t syscon_target_power_header_route_set(uint32_t direction)
{
    LOG(3, "Enable 5V booster");
    syscon_target_power_boost_set(1);
    syscon_target_timer_delay(20);
    uint32_t voltage = syscon_target_power_measure(13);
    if ((int32_t)voltage <= 4499)
        LOG(1, "5V booster: output voltage is too low %d", voltage);
    if (direction == 1) {
        LOG(3, "Set 5V input");
        syscon_target_pin_write(25, 0);
        syscon_target_pin_write(40, 1);
    } else if (direction == 2) {
        LOG(3, "Set 5V output");
        syscon_target_pin_write(40, 0);
        syscon_target_pin_write(25, 1);
    } else {
        syscon_target_timer_delay(20);
        syscon_target_pin_write(25, 0);
        syscon_target_pin_write(40, 0);
    }
    if (syscon_target_power_header_route() != direction) {
        uint32_t actual = syscon_target_power_header_route();
        LOG(1, "Setting 5V direction failed: %d -> %d", actual, direction);
    }
    if (syscon_target_power_header_route() != direction)
        power_assert(0x1e6, "power_manager_get_5v_dir() == dir");
    return (uint64_t)direction << 32;
}
uint32_t syscon_target_power_header_default(void)
{
    if (syscon_target_power_header_route() == 1) {
        LOG(3, "5V header is externally driven, leaving as input");
        return 0;
    }
    LOG(3, "Keeping 5V header powered while the modem is off");
    return (uint32_t)syscon_target_power_header_route_set(2);
}
uint32_t syscon_target_power_usb_isolate(uint32_t isolate)
{
    LOG(3, "Set fake usb cable: %s", isolate ? "ON" : "OFF");
    uint32_t a = syscon_target_pin_write(32, isolate != 0),
             b = syscon_target_pin_write(28, isolate == 0);
    return a + b;
}
uint64_t syscon_target_power_vbus_route_set(uint32_t source)
{
    uint32_t old = syscon_target_power_vbus_route();
    if (old == source) {
        const char *name = syscon_power_name(syscon_power_names.vbus_route, old);
        LOG(1, "VBUS_MAIN not changed: %s", name);
        return (uint64_t)source << 32;
    }
    const char *next_name = syscon_power_name(syscon_power_names.vbus_route, source);
    const char *previous_name = syscon_power_name(syscon_power_names.vbus_route, old);
    LOG(3, "VBUS_MAIN:%s -> %s", previous_name, next_name);
    if (source <= 1) {
        syscon_target_pin_write(35, source);
        syscon_target_pin_write(26, 0);
        syscon_target_power_usb_isolate(0);
    } else if (source == 2) {
        syscon_target_pin_write(26, 1);
        syscon_target_pin_write(35, 0);
        syscon_target_power_usb_isolate(1);
    }
    if (syscon_target_power_vbus_route() != source)
        power_assert(0x168, "currSource == source");
    return (uint64_t)(uintptr_t)next_name << 32;
}
uint32_t syscon_target_power_usb_release_callback(void)
{
    uint32_t result = syscon_target_power_usb_isolate(0);
    if ((int32_t)result < 0)
        LOG(1, "power_manager_set_fake_usb_cable(POWER_MANAGER_FAKE_USB_CABLE_OFF) failed: %d",
            result);
    uint64_t now = syscon_target_now();
    syscon_usb_reattach_state.released_low = (uint32_t)now;
    syscon_usb_reattach_state.released_high = (uint32_t)(now >> 32);
    syscon_usb_reattach_state.active = 0;
    LOG(3, "USB re-attach: done, settling for %dms", 2000u);
    return 1;
}
uint32_t syscon_target_power_usb_assert_callback(void)
{
    LOG(3, "USB re-attach: presenting a detach for %dms", 250u);
    uint32_t result = syscon_target_power_usb_isolate(1);
    if ((int32_t)result < 0)
        LOG(1, "power_manager_set_fake_usb_cable(POWER_MANAGER_FAKE_USB_CABLE_ON) failed: %d",
            result);
    return 1;
}
uint32_t syscon_target_power_shutdown_busy(void)
{
    uint32_t active = syscon_usb_reattach_state.active;
    if (active)
        return active;
    uint32_t lo = syscon_usb_reattach_state.released_low,
             hi = syscon_usb_reattach_state.released_high;
    if (!(lo | hi))
        return 0;
    uint64_t now = syscon_target_now();
    lo = syscon_usb_reattach_state.released_low;
    hi = syscon_usb_reattach_state.released_high;
    return now - ((uint64_t)hi << 32 | lo) < 2000u;
}
uint32_t syscon_target_power_shutdown_request(void)
{
    if (syscon_target_power_shutdown_busy()) {
        LOG(2, "USB re-attach already in progress");
        return UINT32_MAX;
    }
    uint32_t voltage = syscon_target_power_measure(16);
    if ((int32_t)voltage <= 4499) {
        LOG(3, "USB-C not attached (%dmV), skipping USB re-attach", voltage);
        return UINT32_MAX;
    }
    if (!syscon_target_power_boost()) {
        LOG(2, "5V booster is off, cannot drive CC - skipping USB re-attach");
        return UINT32_MAX;
    }
    const syscon_action actions[] = {
        {.kind = 0, .value = (uint32_t)(uintptr_t)syscon_target_power_usb_assert_callback},
        {.kind = 1, .value = 250},
        {.kind = 0, .value = (uint32_t)(uintptr_t)syscon_target_power_usb_release_callback},
    };
    syscon_usb_reattach_state.active = 1;
    syscon_usb_reattach_state.released_low = 0;
    syscon_usb_reattach_state.released_high = 0;
    if (syscon_target_tasks_submit(actions, sizeof(actions) / sizeof(actions[0])) < 0) {
        LOG(1, "No task slot for USB re-attach");
        syscon_usb_reattach_state.active = 0;
        return UINT32_MAX;
    }
    return 0;
}
uint32_t syscon_target_power_battery_detect(void)
{
    uint32_t voltage = syscon_target_power_measure(14), type;
    if ((int32_t)voltage > 2999) {
        LOG(3, "battery voltage: %d", voltage);
        type = 1;
    } else {
        uint32_t result = (uint32_t)syscon_target_power_battery_route_set(2);
        if ((int32_t)result < 0)
            LOG(1, "power_manager_set_modem_vbatt_source(MODEM_VBAT_SOURCE_DCDC) failed: %d",
                result);
        syscon_target_power_ntc_set(1);
        result = syscon_target_power_battery_sense_set(0);
        if ((int32_t)result < 0)
            LOG(1, "power_manager_set_ntc_det_ctrl(POWER_MANAGER_NTC_DETECT_ENABLE) failed: %d",
                result);
        voltage = syscon_target_power_measure(23);
        LOG(3, "ntc voltage: %d", voltage);
        result = (uint32_t)syscon_target_power_battery_route_set(0);
        if ((int32_t)result < 0)
            LOG(1, "power_manager_set_modem_vbatt_source(MODEM_VBAT_SOURCE_NONE) failed: %d",
                result);
        result = syscon_target_power_battery_sense_set(1);
        type = ((voltage - 400u) > 800u) + 1u;
        if ((int32_t)result < 0)
            LOG(1, "power_manager_set_ntc_det_ctrl(POWER_MANAGER_NTC_DETECT_DISABLE) failed: %d",
                result);
    }
    const char *name = syscon_power_name(syscon_power_names.battery, type);
    LOG(3, "battery: %s", name);
    syscon_target_retained_set_battery(type);
    syscon_target_power_ntc_set(0);
    return type;
}
