/* Source-backed original ARM32 SG560D entries, including diagnostics. */
#include "sg560d_target.h"
#include "modem_state.h"
#include "runtime_memory.h"
#include "scheduling_target.h"
#include "power_manager_target.h"
#include "power_policy_target.h"
#include "power_state.h"
#include "mspm0_core_target.h"
#include "uart_hal_target.h"
#include "uart_ring_target.h"
#include "hal_helpers.h"
#include "ioexpander_target.h"
#include "rgb_target.h"
#include "power_key_target.h"
#include "adc_target.h"
#include "diagnostics_target.h"
#include "application_target.h"
#include "protocol_target.h"
#include "logger_target.h"
#define ADDRESS(p) ((uint32_t)(uintptr_t)(p))
#define LOG(level, format, ...) syscon_target_logger(level, "560D", format, ##__VA_ARGS__)
static uint64_t read64(const volatile syscon_modem_timestamp *clock)
{
    uint32_t lo = clock->low, hi = clock->high;
    return (uint64_t)lo | ((uint64_t)hi << 32);
}
static void write64(volatile syscon_modem_timestamp *clock, uint64_t value)
{
    clock->low = (uint32_t)value;
    clock->high = (uint32_t)(value >> 32);
}
static void check(uint32_t line, const char *condition)
{
    syscon_target_assert(ADDRESS("sg560d.cpp"), line, ADDRESS(condition));
}
static int32_t measure(uint32_t pin)
{
    return (int32_t)syscon_target_power_measure(pin);
}
void syscon_target_modem_uart_stop(void)
{
    if (syscon_modem_parser.enabled) {
        if (syscon_target_uart_deinit(1))
            check(0x105, "success == 0");
        syscon_rt_memset((void *)syscon_modem_scratch, 0, sizeof(syscon_modem_scratch));
        syscon_modem_parser.enabled = 0;
    }
    uint8_t config[12] = {0};
    config[5] = 2;
    uint32_t descriptor = syscon_hal_uart_lookup(1);
    if (!descriptor)
        check(0x116, "uart != nullptr");
    syscon_target_gpio_config(*(const uint8_t *)(uintptr_t)descriptor, ADDRESS(config));
    syscon_target_gpio_config(*(const uint8_t *)(uintptr_t)(descriptor + 3), ADDRESS(config));
}
void syscon_target_modem_uart_start(void)
{
    if (syscon_modem_parser.enabled)
        return;
    const uint8_t config[9] = {0, 0, 9, 0, 0, 0xc2, 1, 0, 0};
    if (syscon_target_uart_init(1, ADDRESS(config)))
        check(0xf8, "success == 0");
    syscon_rt_memset((void *)syscon_modem_scratch, 0, sizeof(syscon_modem_scratch));
    syscon_modem_parser.enabled = 1;
}
uint32_t syscon_target_modem_power_check(void)
{
    int32_t battery = (int32_t)syscon_target_power_battery_detect();
    int32_t route = (int32_t)syscon_target_power_battery_route();
    LOG(3, "Current VBATT source: %s", syscon_power_name(syscon_power_names.battery_route, route));
    if (measure(15) > 1699) {
        LOG(1, "cannot change power source when the modem is powered up", 1699);
        check(0x152, "false");
    }
    if (!syscon_target_hwrevision_new()) {
        if (route)
            check(0x159, "vbattSrc == MODEM_VBAT_SOURCE_NONE");
    } else if (route)
        LOG(1, "Modem VBAT is not off due to work around issue");
    uint32_t direction = syscon_target_power_header_route();
    int32_t header = measure(13), battery_mv = measure(14);
    uint32_t input = header > 4500 && direction < 2;
    if (input)
        LOG(3, "5V input ON");
    else
        LOG(3, "5V input OFF");
    int32_t usb = measure(16);
    if (usb <= 4499)
        LOG(2, "VUSB: USB-C is not attached %d", usb);
    int32_t status = (int32_t)syscon_target_power_header_route_set(input ? 1 : 2);
    if (status < 0) {
        if (input)
            LOG(1, "power_manager_set_5v_dir(POWER_MANAGER_HEADER_5V_INPUT) failed: %d", status);
        else
            LOG(1, "power_manager_set_5v_dir(POWER_MANAGER_HEADER_5V_OUTPUT) failed: %d", status);
    }
    if (battery == 1) {
        if (battery_mv < 2000) {
            if (syscon_target_hwrevision_new()) {
                LOG(1, "Working around dead battery issue");
                status = (int32_t)syscon_target_power_battery_route_set(2);
                if (status < 0)
                    LOG(1,
                        "power_manager_set_modem_vbatt_source(MODEM_VBAT_SOURCE_DCDC) failed: %d",
                        status);
                syscon_modem_runtime.temporary_dcdc = 1;
            }
        } else {
            status = (int32_t)syscon_target_power_battery_route_set(1);
            if (status < 0)
                LOG(1, "power_manager_set_modem_vbatt_source(MODEM_VBAT_SOURCE_BATTERY) failed: %d",
                    status);
        }
    } else {
        status = (int32_t)syscon_target_power_battery_route_set(2);
        if (status < 0)
            LOG(1, "power_manager_set_modem_vbatt_source(MODEM_VBAT_SOURCE_DCDC) failed: %d",
                status);
    }
    syscon_target_power_vbus_route_set(usb <= 4499 && input && battery == 1 ? 2 : 1);
    syscon_target_power_report(ADDRESS(syscon_target_mfg_logger));
    syscon_modem_runtime.expected_state = 1;
    write64(&syscon_modem_runtime.transition_deadline, syscon_target_now() + 3000);
    LOG(3, "power turned on");
    return 1;
}
uint32_t syscon_target_modem_fct_complete(void)
{
    LOG(3, "FCT mode setup complete");
    return 1;
}
uint32_t syscon_target_modem_volume_release(void)
{
    LOG(3, "releasing volume down");
    syscon_target_pin_write(29, 1);
    return 1;
}
uint32_t syscon_target_modem_usbboot_release(void)
{
    LOG(3, "setting USB_BOOT back to 0");
    syscon_target_gpio_write(11, 0);
    return 1;
}
uint32_t syscon_target_modem_powerkey_release_task(void)
{
    LOG(3, "boot 2");
    syscon_target_gpio_write(8, 0);
    return 1;
}
uint32_t syscon_target_modem_normal_key_release(void)
{
    return syscon_target_modem_powerkey_release_task();
}
uint32_t syscon_target_modem_special_key_release(void)
{
    return syscon_target_modem_powerkey_release_task();
}
uint32_t syscon_target_modem_edl_key_release(void)
{
    return syscon_target_modem_powerkey_release_task();
}
void syscon_target_modem_pins_off(void)
{
    const uint8_t gpio[12] = {0};
    const syscon_io_config expander = {0, 0, 1};
    syscon_target_gpio_config(8, ADDRESS(gpio));
    syscon_target_gpio_config(11, ADDRESS(gpio));
    syscon_target_ioexpander_configure(14, &expander);
    syscon_target_ioexpander_configure(4, &expander);
}
void syscon_target_modem_pins_on(void)
{
    uint8_t gpio[12] = {0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0};
    const syscon_io_config expander = {1, 1, 1};
    syscon_target_gpio_config(8, ADDRESS(gpio));
    syscon_target_gpio_config(11, ADDRESS(gpio));
    syscon_target_ioexpander_configure(14, &expander);
    syscon_target_ioexpander_configure(4, &expander);
    gpio[4] = 0;
    gpio[5] = 2;
    syscon_target_gpio_config(18, ADDRESS(gpio));
    syscon_target_gpio_config(19, ADDRESS(gpio));
    syscon_target_gpio_config(20, ADDRESS(gpio));
    syscon_target_modem_uart_stop();
}
uint32_t syscon_target_modem_retry_delay(uint32_t reason, uint32_t attempts)
{
    int32_t temperature = (int32_t)syscon_target_adc_temperature();
    uint32_t initial = reason < 7 ? syscon_modem_retry_delays[reason] : 900000, delay = initial;
    if (temperature >= 500) {
        if (initial < 120000)
            delay = 120000;
        if (initial <= 119999)
            LOG(3, "board at %d.%dC - using thermal backoff for %s", temperature / 10,
                temperature % 10, syscon_power_name(syscon_power_names.shutdown, reason));
    }
    for (uint32_t i = 0; i != attempts; i++) {
        if (delay > 449999)
            return 900000;
        delay *= 2;
    }
    return delay;
}
void syscon_target_modem_retry_schedule(uint32_t reason)
{
    uint32_t continuing =
        syscon_modem_runtime.retry_active != 0 && syscon_modem_runtime.retry_reason == reason;
    syscon_modem_runtime.retry_reason = (uint8_t)reason;
    if (reason == 0 || reason - 3 < 4) {
        if (!continuing)
            syscon_modem_runtime.retry_count = 0;
        syscon_modem_runtime.retry_active = 1;
        uint32_t delay = syscon_target_modem_retry_delay(reason, syscon_modem_runtime.retry_count);
        write64(&syscon_modem_runtime.retry_deadline, syscon_target_now() + delay);
        LOG(3, "%s - auto-boot %s (if enabled), next attempt in %ds, attempts so far %d",
            syscon_power_name(syscon_power_names.shutdown, reason),
            continuing ? ADDRESS("continuing") : ADDRESS("pending"), delay / 1000,
            syscon_modem_runtime.retry_count);
    }
}
#define ACTION(fn) {0, {0, 0, 0}, (uint32_t)(uintptr_t)(fn)}
#define DELAY(ms) {1, {0, 0, 0}, (ms)}
static const syscon_action boot_actions[] = {ACTION(syscon_target_modem_prepare_normal),
                                             DELAY(2000),
                                             ACTION(syscon_target_modem_normal_key_release),
                                             ACTION(syscon_target_modem_prepare_edl),
                                             DELAY(2000),
                                             ACTION(syscon_target_modem_edl_key_release),
                                             ACTION(syscon_target_modem_usbboot_release),
                                             ACTION(syscon_target_modem_prepare_special),
                                             DELAY(2000),
                                             ACTION(syscon_target_modem_special_key_release),
                                             DELAY(100),
                                             ACTION(syscon_target_modem_volume_release),
                                             DELAY(5000),
                                             ACTION(syscon_target_modem_fct_first_reset_pulse),
                                             DELAY(200),
                                             ACTION(syscon_target_modem_fct_second_reset_pulse),
                                             DELAY(200),
                                             ACTION(syscon_target_modem_fct_powerkey_pulse),
                                             ACTION(syscon_target_modem_fct_complete)};
uint32_t syscon_target_modem_poweron(void)
{
    if (syscon_modem_runtime.current_state) {
        LOG(1, "sg560d_power_on_normal ignored, modem is not off");
        return UINT32_MAX;
    }
    syscon_target_shutdown_set(0);
    syscon_modem_runtime.retry_active = 0;
    syscon_modem_runtime.retry_reason = 0;
    syscon_target_modem_pins_on();
    syscon_target_wakeup_enable(0);
    syscon_action actions[3];
    syscon_rt_memcpy(actions, boot_actions, sizeof(actions));
    if (syscon_target_tasks_submit(actions, 3) < 0)
        LOG(3, "Failed to start NORMAL mode task");
    return 0;
}
uint32_t syscon_target_modem_edl(void)
{
    if (syscon_modem_runtime.current_state) {
        LOG(1, "sg560d_power_on_edl ignored, modem is not off");
        return UINT32_MAX;
    }
    syscon_target_shutdown_set(0);
    syscon_modem_runtime.retry_active = 0;
    syscon_modem_runtime.retry_reason = 0;
    syscon_target_modem_pins_on();
    syscon_target_wakeup_enable(0);
    syscon_action actions[4];
    syscon_rt_memcpy(actions, boot_actions + 3, sizeof(actions));
    if (syscon_target_tasks_submit(actions, 4) < 0)
        LOG(3, "Failed to start EDL mode task");
    return 0;
}
uint32_t syscon_target_modem_special_boot(uint32_t fct)
{
    if (syscon_modem_runtime.current_state) {
        LOG(1, "sg560d_power_on_fastboot_or_fct ignored, modem is not off");
        return UINT32_MAX;
    }
    syscon_target_shutdown_set(0);
    syscon_modem_runtime.retry_active = 0;
    syscon_modem_runtime.retry_reason = 0;
    syscon_target_modem_pins_on();
    syscon_target_wakeup_enable(0);
    syscon_modem_boot.label = fct ? syscon_modem_fct_label : syscon_modem_fastboot_label;
    syscon_modem_boot.mode = fct ? 5 : 3;
    syscon_action actions[12];
    syscon_rt_memcpy(actions, boot_actions + 7, sizeof(actions));
    if (syscon_target_tasks_submit(actions, fct ? 12 : 5) < 0)
        LOG(3, "Failed to start %s mode task", syscon_modem_boot.label);
    return 0;
}
uint32_t syscon_target_modem_fct(void)
{
    return syscon_target_modem_special_boot(1);
}
uint32_t syscon_target_modem_fct_callback(void)
{
    syscon_target_modem_special_boot(1);
    return 1;
}
uint32_t syscon_target_modem_fastboot(void)
{
    return syscon_target_modem_special_boot(0);
}
void syscon_target_modem_wake_schedule(uint32_t seconds)
{
    if (!seconds) {
        if (read64(&syscon_modem_timing.wake_deadline))
            LOG(3, "Timed wake cancelled");
        write64(&syscon_modem_timing.wake_deadline, 0);
    } else {
        write64(&syscon_modem_timing.wake_deadline, syscon_target_now() + (uint64_t)seconds * 1000);
        LOG(3, "Timed wake armed: %ds from now", seconds);
    }
}
int32_t syscon_target_modem_wake_remaining(void)
{
    uint64_t now = syscon_target_now(), deadline = read64(&syscon_modem_timing.wake_deadline);
    if (!deadline)
        return -1;
    return now >= deadline ? 0 : (int32_t)((deadline - now) / 1000);
}
uint32_t syscon_target_modem_off(void)
{
    return syscon_modem_runtime.current_state == 0;
}
uint32_t syscon_target_modem_mode_name(uint32_t mode)
{
    const char *const names[] = {"HARD_OFF", "NORMAL", "FASTBOOT", "EDL", "FCT"};
    uint32_t index = (uint8_t)(mode - 1);
    return index < 5 ? ADDRESS(names[index]) : ADDRESS("UNKNOWN");
}
uint32_t syscon_target_modem_set_mode(uint32_t mode)
{
    LOG(3, "setting mode to %s", syscon_target_modem_mode_name(mode));
    syscon_modem_timing.mode = (uint8_t)mode;
    syscon_target_retained_set_modem(mode);
    uint32_t key = 0;
    switch (mode) {
    case 1:
        syscon_target_rgb_preset(0, 0);
        key = 1;
        break;
    case 2:
        syscon_target_rgb_preset(4, 0);
        break;
    case 3:
        syscon_target_rgb_preset(1, 0);
        key = 1;
        break;
    case 4:
        syscon_target_rgb_preset(2, 0);
        key = 1;
        break;
    case 5:
        syscon_target_rgb_preset(3, 0);
        break;
    }
    syscon_target_powerkey_mode(key);
    return 0;
}
uint32_t syscon_target_modem_poweroff(uint32_t force)
{
    if (syscon_target_tasks_active()) {
        LOG(3, "sg560d_power_off aborting whilst powering on");
        return 0;
    }
    int32_t voltage = measure(15);
    if (voltage > 1699 || force) {
        LOG(3, "powering down by cutting power");
        int32_t status = (int32_t)syscon_target_power_vbus_route_set(0);
        if (status < 0)
            LOG(1, "power_manager_set_vbus_source(MODEM_VBUS_SOURCE_NONE) failed: %d", status);
        status = (int32_t)syscon_target_power_battery_route_set(0);
        if (status < 0)
            LOG(1, "power_manager_set_modem_vbatt_source(MODEM_VBAT_SOURCE_NONE) failed: %d",
                status);
        if (syscon_target_keep_5v_when_off()) {
            status = (int32_t)syscon_target_power_header_default();
            if (status < 0)
                LOG(1, "power_manager_5v_header_keep_on() failed: %d", status);
        } else {
            status = (int32_t)syscon_target_power_header_route_set(0);
            if (status < 0)
                LOG(1, "power_manager_set_5v_dir(POWER_MANAGER_HEADER_5V_DISCONNECTED) failed: %d",
                    status);
            status = (int32_t)syscon_target_power_boost_set(0);
            if (status < 0)
                LOG(1, "power_manager_set_5v_booster_enable(false) failed: %d", status);
        }
        syscon_target_modem_set_mode(1);
        syscon_modem_runtime.expected_state = 3;
        write64(&syscon_modem_runtime.transition_deadline, syscon_target_now() + 3000);
    }
    syscon_target_modem_uart_stop();
    syscon_target_modem_pins_off();
    syscon_target_wakeup_enable(1);
    syscon_modem_boot.restarting = 0;
    syscon_modem_runtime.temporary_dcdc = 0;
    write64(&syscon_modem_runtime.battery_restore_deadline, 0);
    return 1;
}
uint32_t syscon_target_modem_prepare_special(void)
{
    LOG(3, "preparing to enter %s", syscon_modem_boot.label);
    uint32_t ok = syscon_target_modem_power_check();
    if (!ok) {
        LOG(1, "powerCheck on failed");
        syscon_target_modem_pins_off();
        syscon_target_wakeup_enable(1);
    } else {
        syscon_target_modem_set_mode(syscon_modem_boot.mode);
        syscon_target_pin_write(29, 0);
        syscon_target_gpio_write(8, 1);
        syscon_modem_timing.special_started = (uint32_t)syscon_target_now();
    }
    return ok;
}
uint32_t syscon_target_modem_prepare_edl(void)
{
    LOG(3, "preparing to enter EDL mode");
    syscon_target_gpio_write(11, 1);
    uint32_t ok = syscon_target_modem_power_check();
    if (!ok) {
        LOG(1, "powerCheck on failed");
        syscon_target_modem_pins_off();
        syscon_target_wakeup_enable(1);
        syscon_target_gpio_write(11, 0);
    } else {
        syscon_target_modem_set_mode(4);
        syscon_target_gpio_write(8, 1);
    }
    return ok;
}
uint32_t syscon_target_modem_prepare_normal(void)
{
    LOG(3, "preparing to enter NORMAL mode");
    uint32_t ok = syscon_target_modem_power_check();
    if (!ok) {
        LOG(1, "powerCheck on failed");
        syscon_target_modem_pins_off();
        syscon_target_wakeup_enable(1);
    } else {
        syscon_target_modem_set_mode(2);
        syscon_target_gpio_write(8, 1);
    }
    return ok;
}
uint32_t syscon_target_modem_init(uint32_t mode)
{
    syscon_target_modem_pins_on();
    int32_t voltage = measure(15);
    if (voltage > 1699) {
        if (mode < 2) {
            LOG(3, "SG560D is on, assuming NORMAL mode", 1699);
            mode = 2;
        }
        syscon_modem_runtime.expected_state = 2;
        syscon_modem_runtime.current_state = 2;
        write64(&syscon_modem_runtime.started, syscon_target_now());
    } else {
        if (mode > 1)
            LOG(1, "SG560D is off, mode  changes from %s to HARD_OFF",
                syscon_target_modem_mode_name(mode));
        mode = 1;
        syscon_modem_runtime.expected_state = 0;
        syscon_modem_runtime.current_state = 0;
    }
    syscon_target_modem_set_mode(mode);
    uint32_t on = syscon_modem_runtime.current_state == 2;
    LOG(3, "Modem power state: %s", on ? ADDRESS("ON") : ADDRESS("OFF"));
    if (on) {
        syscon_target_modem_uart_start();
        syscon_target_wakeup_enable(0);
    } else {
        syscon_target_modem_pins_off();
        syscon_target_wakeup_enable(1);
        if (syscon_target_keep_5v_when_off()) {
            int32_t status = (int32_t)syscon_target_power_header_default();
            if (status < 0)
                LOG(1, "power_manager_5v_header_keep_on() failed: %d", status);
        }
    }
    return on;
}
void syscon_target_modem_key_assert(void)
{
    LOG(3, "PWR-KEY pressed");
    syscon_target_gpio_write(8, 1);
}
void syscon_target_modem_key_release(void)
{
    LOG(3, "PWR-KEY released");
    syscon_target_gpio_write(8, 0);
}
uint32_t syscon_target_modem_key_pulse(uint32_t pin, uint32_t initial)
{
    syscon_target_pin_write((uint8_t)pin, initial);
    syscon_target_timer_delay(250);
    syscon_target_pin_write((uint8_t)pin, initial ^ 1);
    return 0;
}
uint32_t syscon_target_modem_fct_powerkey_pulse(void)
{
    LOG(3, "pressing power key to enter FCT mode");
    syscon_target_modem_key_pulse(8, 1);
    return 1;
}
uint32_t syscon_target_modem_fct_second_reset_pulse(void)
{
    LOG(3, "second quick volume up press");
    syscon_target_modem_key_pulse(39, 0);
    return 1;
}
uint32_t syscon_target_modem_fct_first_reset_pulse(void)
{
    LOG(3, "first quick volume up press");
    syscon_target_modem_key_pulse(39, 0);
    return 1;
}
uint32_t syscon_target_modem_raw_send(uint32_t data, uint32_t length)
{
    return syscon_target_uart_write_buffer(1, data, length);
}

static void update_power_transitions(void)
{
    syscon_target_shutdown_poll();
    int32_t v18 = measure(15);
    if (v18 > 1699)
        syscon_target_power_minimum_update();
    if (read64(&syscon_modem_runtime.battery_restore_deadline) &&
        syscon_target_now() >= read64(&syscon_modem_runtime.battery_restore_deadline)) {
        write64(&syscon_modem_runtime.battery_restore_deadline, 0);
        syscon_modem_runtime.temporary_dcdc = 0;
        LOG(3, "dead battery: handing the pack back");
        syscon_target_power_battery_route_set(1);
        syscon_target_power_minimum_reset();
    }
    if (v18 > 1699) {
        if (!syscon_modem_runtime.current_state) {
            if (syscon_modem_runtime.expected_state == 1) {
                syscon_modem_runtime.current_state = 2;
                syscon_modem_runtime.expected_state = 2;
                write64(&syscon_modem_runtime.transition_deadline, 0);
                syscon_target_modem_uart_start();
                uint32_t vph = (uint32_t)measure(12), route = syscon_target_power_battery_route();
                LOG(3, "Modem 1V8 up: vph %dmV vbatt src %s", vph,
                    syscon_power_name(syscon_power_names.battery_route, route));
                if (syscon_modem_runtime.temporary_dcdc)
                    write64(&syscon_modem_runtime.battery_restore_deadline,
                            syscon_target_now() + 50);
                syscon_target_power_minimum_reset();
                write64(&syscon_modem_runtime.started, syscon_target_now());
                if (read64(&syscon_modem_timing.wake_deadline)) {
                    LOG(3, "Timed wake cancelled - modem is up");
                    write64(&syscon_modem_timing.wake_deadline, 0);
                }
                if (syscon_modem_boot.restarting) {
                    syscon_modem_boot.restarting = 0;
                    uint32_t reason = syscon_target_shutdown_reason(),
                             stale = syscon_target_shutdown_stale();
                    if (reason == 1)
                        LOG(3, "Modem power GOOD: reboot confirmed%s",
                            stale ? ADDRESS(" (stale)") : ADDRESS(""));
                    else
                        LOG(2, "Modem power WARNING: reboot detected but reason was %s%s",
                            syscon_power_name(syscon_power_names.shutdown, reason),
                            stale ? ADDRESS(" (stale)") : ADDRESS(""));
                    syscon_target_shutdown_set(0);
                    syscon_modem_runtime.retry_active = 0;
                    syscon_modem_runtime.retry_reason = 0;
                    if (syscon_modem_timing.mode == 5) {
                        uint32_t elapsed =
                            (uint32_t)syscon_target_now() - syscon_modem_timing.special_started;
                        if (elapsed) {
                            if (elapsed > 14999) {
                                LOG(1, "FCT crash", elapsed);
                                syscon_target_modem_poweroff(1);
                                const syscon_action retry[] = {
                                    DELAY(3000), ACTION(syscon_target_modem_fct_callback)};
                                if (syscon_target_tasks_submit(retry, 2) < 0)
                                    LOG(3, "Failed to retry_fct_mode task");
                            } else
                                LOG(3, "FCT reboot %d", elapsed);
                            goto transition_done;
                        }
                        LOG(3, "FCT timer not set", elapsed);
                    }
                    if (syscon_modem_timing.mode != 2) {
                        LOG(3, "Modem rebooted, setting mode to NORMAL", syscon_modem_timing.mode);
                        syscon_target_modem_set_mode(2);
                    }
                } else
                    LOG(3, "Modem power GOOD: power on");
            } else if (!syscon_modem_runtime.expected_state) {
                LOG(1, "Modem power ERROR: unexpected power on");
                syscon_modem_runtime.current_state = 2;
                syscon_modem_runtime.expected_state = 2;
                write64(&syscon_modem_runtime.transition_deadline, 0);
                syscon_target_modem_uart_start();
                syscon_target_wakeup_enable(0);
                syscon_target_modem_set_mode(2);
            }
        }
    } else if (syscon_modem_runtime.current_state == 2) {
        if (syscon_modem_runtime.expected_state == 3) {
            syscon_modem_runtime.expected_state = 0;
            write64(&syscon_modem_runtime.transition_deadline, 0);
            syscon_modem_runtime.current_state = 0;
            syscon_target_modem_uart_stop();
            write64(&syscon_modem_runtime.started, 0);
            LOG(3, "Modem power GOOD: power off");
        } else if (syscon_modem_runtime.expected_state == 2) {
            syscon_target_power_minimum_update();
            uint32_t floor = syscon_target_power_minimum();
            uint32_t battery = (uint32_t)measure(14);
            if (!syscon_target_shutdown_reason() && floor <= 2499)
                syscon_target_shutdown_set(6);
            uint32_t reason = syscon_target_shutdown_reason(),
                     stale = syscon_target_shutdown_stale();
            LOG(2,
                "Modem power WARNING: unexpected power off (reason: %s%s) vph floor %dmV vbat now "
                "%dmV",
                syscon_power_name(syscon_power_names.shutdown, reason),
                stale ? ADDRESS(", stale") : ADDRESS(""), floor, battery);
            syscon_target_power_minimum_reset();
            reason = syscon_target_shutdown_active();
            syscon_modem_runtime.expected_state = 1;
            syscon_modem_boot.restarting = 1;
            write64(&syscon_modem_runtime.started, 0);
            syscon_modem_runtime.current_state = 0;
            write64(&syscon_modem_runtime.transition_deadline, syscon_target_now() + 250);
            syscon_target_modem_retry_schedule(reason);
        }
    }
transition_done:
    if (read64(&syscon_modem_runtime.transition_deadline) &&
        syscon_target_now() > read64(&syscon_modem_runtime.transition_deadline)) {
        if (!syscon_modem_boot.restarting) {
            if (!syscon_modem_runtime.current_state && syscon_modem_runtime.expected_state == 1) {
                LOG(1, "Modem power ERROR: power on never completed");
                uint32_t mode = syscon_modem_timing.mode;
                syscon_target_modem_poweroff(1);
                if (mode - 3 > 2)
                    syscon_target_modem_retry_schedule(syscon_target_shutdown_active());
            } else
                LOG(1, "Modem power state error: timeout waiting for power state change");
        } else if (!syscon_modem_runtime.current_state &&
                   syscon_modem_runtime.expected_state == 1) {
            syscon_modem_boot.restarting = 0;
            uint32_t reason = syscon_target_shutdown_active();
            if (reason == 1) {
                LOG(3, "Reboot timeout - manually triggering power on");
                syscon_target_modem_poweron();
            } else {
                if ((uint8_t)(reason - 3) < 4 || !reason)
                    LOG(3, "Modem power off confirmed: did not reboot. %s has pending auto-boot",
                        syscon_power_name(syscon_power_names.shutdown, reason));
                else
                    LOG(3, "Modem power off confirmed: did not reboot");
                syscon_target_modem_poweroff(1);
            }
        } else
            LOG(1, "Modem power state error: timeout waiting for power state change");
        syscon_modem_runtime.expected_state = syscon_modem_runtime.current_state;
        write64(&syscon_modem_runtime.transition_deadline, 0);
    }
}

/* Three consecutive high samples assert a color; eight low samples clear it. */
static void update_rgb_feedback(void)
{
    uint8_t samples[3];
    samples[0] = syscon_target_gpio_read(18) == 1;
    samples[1] = syscon_target_gpio_read(19) == 1;
    samples[2] = syscon_target_gpio_read(20) == 1;
    for (unsigned i = 0; i < 3; i++)
        syscon_modem_runtime.rgb_history[i] =
            (uint8_t)((syscon_modem_runtime.rgb_history[i] << 1) | samples[i]);
    uint8_t rgb[3];
    syscon_rt_memset(rgb, 0, 3);
    syscon_rt_memcpy(rgb, (void *)syscon_modem_boot.rgb, 3);
    for (unsigned i = 0; i < 3; i++) {
        if (!syscon_modem_runtime.rgb_history[i])
            rgb[i] = 0;
        else if ((syscon_modem_runtime.rgb_history[i] & 7) == 7)
            rgb[i] = 1;
    }
    if (syscon_rt_memcmp((void *)syscon_modem_boot.rgb, rgb, 3)) {
        LOG(3, "RGB status changed: R:%s G:%s B:%s", rgb[0] ? ADDRESS("ON") : ADDRESS("OFF"),
            rgb[1] ? ADDRESS("ON") : ADDRESS("OFF"), rgb[2] ? ADDRESS("ON") : ADDRESS("OFF"));
        syscon_modem_runtime.rgb_changed = (uint32_t)syscon_target_now();
        if (!rgb[0] && rgb[1] && !rgb[2])
            syscon_modem_runtime.green_changed = (uint32_t)syscon_target_now();
        if (!rgb[0] && !rgb[1] && !rgb[2] &&
            syscon_target_now() - (uint64_t)syscon_modem_runtime.green_changed < 150) {
            LOG(3, "green LED was on for less than 150ms", 0);
            LOG(3, "boot confirmed");
        }
        syscon_modem_boot.rgb[0] = rgb[0];
        syscon_modem_boot.rgb[1] = rgb[1];
        syscon_modem_boot.rgb[2] = rgb[2];
    }
    uint32_t green = 0, cyan = 0, yellow = 0;
    if (rgb[1]) {
        green = rgb[1];
        if (!rgb[0]) {
            if (rgb[2]) {
                green = 0;
                cyan = rgb[2];
            }
        } else {
            green = 0;
            yellow = rgb[2] ^ 1;
        }
    }
    uint32_t stable = syscon_modem_runtime.rgb_changed &&
                      syscon_target_now() - (uint64_t)syscon_modem_runtime.rgb_changed >= 1001;
    uint32_t preset = syscon_target_rgb_state();
    if (stable) {
        uint32_t desired = green ? 5 : cyan ? 6 : yellow ? 7 : 0;
        if (desired && preset != desired) {
            LOG(3, "changing RGB theme from %d to %d", preset, desired);
            syscon_target_rgb_preset(desired, 0);
        } else
            LOG(3, "not changing RGB theme from %d", preset);
        syscon_modem_runtime.rgb_changed = 0;
    }
}

static void update_automatic_start(void)
{
    int32_t usb = measure(16);
    uint32_t present = usb > 4499;
    if (!syscon_modem_runtime.initialized) {
        syscon_modem_runtime.usb_present = (uint8_t)present;
        syscon_modem_runtime.initialized = 1;
    }
    uint8_t current = syscon_modem_runtime.current_state,
            expected = syscon_modem_runtime.expected_state;
    uint32_t automatic = syscon_target_auto_boot();
    if (!current && !expected) {
        if (read64(&syscon_modem_timing.wake_deadline) &&
            syscon_target_now() >= read64(&syscon_modem_timing.wake_deadline)) {
            int32_t temperature = (int32_t)syscon_target_adc_temperature(), header = measure(13);
            uint32_t reason = syscon_target_shutdown_reason();
            uint64_t age = syscon_target_shutdown_elapsed();
            uint32_t permitted = 0;
            if (temperature < 500) {
                if (reason == 3)
                    permitted =
                        (usb > 4499 || header > 4499) && age >= syscon_modem_retry_delays[reason];
                else if ((uint8_t)(reason - 3) < 4 || !reason)
                    permitted = age >= syscon_modem_retry_delays[reason];
                else
                    permitted = 1;
            }
            if (permitted) {
                LOG(3, "Timed wake elapsed - powering on");
                write64(&syscon_modem_timing.wake_deadline, 0);
                syscon_target_modem_poweron();
            } else if (syscon_target_now() >= read64(&syscon_modem_runtime.wake_warning_deadline)) {
                write64(&syscon_modem_runtime.wake_warning_deadline, syscon_target_now() + 60000);
                const char *name = syscon_power_name(syscon_power_names.shutdown, reason);
                uint64_t elapsed = syscon_target_shutdown_elapsed();
                LOG(2, "Timed wake is due but deferred - %s %ds ago, board %d.%dC", name,
                    (uint32_t)(elapsed / 1000), temperature / 10, temperature % 10);
            }
        }
        if (automatic && syscon_modem_runtime.retry_active &&
            !syscon_target_power_shutdown_busy()) {
            if (syscon_target_now() >= read64(&syscon_modem_runtime.retry_deadline)) {
                uint32_t blocked = 0;
                if (syscon_modem_runtime.retry_reason == 3) {
                    int32_t header = measure(13);
                    blocked = usb <= 4499 && header <= 4499;
                }
                if (!blocked) {
                    uint8_t reason = syscon_modem_runtime.retry_reason;
                    syscon_modem_runtime.retry_count = syscon_modem_runtime.retry_count + 1;
                    uint32_t delay =
                        syscon_target_modem_retry_delay(reason, syscon_modem_runtime.retry_count);
                    write64(&syscon_modem_runtime.retry_deadline, syscon_target_now() + delay);
                    LOG(3, "Auto-boot attempt %d for %s, next in %ds if this one fails",
                        syscon_modem_runtime.retry_count,
                        syscon_power_name(syscon_power_names.shutdown, reason), delay / 1000);
                    syscon_target_modem_poweron();
                    syscon_modem_runtime.retry_reason = reason;
                    syscon_modem_runtime.retry_active = 1;
                    syscon_modem_runtime.usb_debouncing = 0;
                }
            }
        }
    }
    if (syscon_modem_runtime.retry_active && read64(&syscon_modem_runtime.started) &&
        syscon_modem_runtime.current_state == 2 &&
        syscon_target_now() - read64(&syscon_modem_runtime.started) > 119999) {
        LOG(3, "Modem up %ds after %d auto-boot attempt(s) - clearing retry state", 120,
            syscon_modem_runtime.retry_count);
        syscon_modem_runtime.retry_count = 0;
        syscon_modem_runtime.retry_active = 0;
        syscon_modem_runtime.retry_reason = 0;
    }
    uint32_t reason = syscon_target_shutdown_active();
    uint32_t owns = syscon_modem_runtime.retry_active && syscon_modem_runtime.retry_reason
                        ? syscon_modem_runtime.retry_active
                        : reason == 2;
    if (!syscon_target_power_shutdown_busy() && !current && !expected && automatic) {
        if (!owns) {
            if (!syscon_modem_runtime.usb_present && present) {
                write64(&syscon_modem_runtime.usb_rise, syscon_target_now());
                syscon_modem_runtime.usb_debouncing = 1;
                LOG(3, "USB connected, starting %dms debounce for auto-boot", 5000);
                goto usb_done;
            }
            if (!syscon_modem_runtime.usb_debouncing) {
                if (present)
                    goto usb_done;
            } else if (present) {
                if (syscon_target_now() - read64(&syscon_modem_runtime.usb_rise) > 4999) {
                    LOG(3, "Auto-boot triggered after USB power restore");
                    syscon_modem_runtime.usb_debouncing = 0;
                    syscon_target_modem_poweron();
                }
                goto usb_done;
            } else
                LOG(3, "USB disconnected during debounce, canceling auto-boot");
        } else if (!syscon_modem_runtime.usb_present && present) {
            uint32_t selected =
                syscon_modem_runtime.retry_active ? syscon_modem_runtime.retry_reason : reason;
            LOG(3, "USB connected but %s owns the boot decision - not auto-booting",
                syscon_power_name(syscon_power_names.shutdown, selected));
        }
    }
    syscon_modem_runtime.usb_debouncing = 0;
usb_done:
    syscon_modem_runtime.usb_present = (uint8_t)present;
}

void syscon_target_modem_poll(void)
{
    update_power_transitions();
    update_rgb_feedback();
    syscon_target_protocol_poll(ADDRESS(&syscon_modem_parser));
    update_automatic_start();
}
