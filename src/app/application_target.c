#include "firmware_version.h"
#include "logger_state.h"
#include "power_state.h"
/* Main loop, key-event queue and wakeup policy. Runs entirely on the MCU. */
#include "application_target.h"
#include "application_state.h"
#include "diagnostics_target.h"
#include "diagnostics_state.h"
#include "scheduling_target.h"
#include "mspm0_core_target.h"
#include "fault_control_target.h"
#include "uart_hal_target.h"
#include "runtime_support.h"
#include "sg560d_target.h"
#include "rgb_target.h"
#include "power_key_target.h"
#include "power_manager_target.h"
#include "power_policy_target.h"
#include "ioexpander_target.h"
#include "protocol_target.h"
#include "uart_ring_target.h"
#include "config_helpers.h"
#include <stdint.h>
#define B(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define ADDRESS(p) ((uint32_t)(uintptr_t)(p))

void syscon_target_timestamp_constructor(void)
{
    syscon_diagnostics_state.last_rate_ms = (uint32_t)syscon_target_now();
}
void syscon_target_queue_destructor(void *queue)
{
    (void)queue;
}
void syscon_target_queue_constructor(void)
{
    syscon_key_events.buffer = ADDRESS(syscon_key_event_buffer);
    syscon_key_events.capacity = SYSCON_KEY_QUEUE_CAPACITY;
    syscon_key_events.read = 0;
    syscon_key_events.write = 0;
    syscon_key_events.full = 0;
    syscon_rt_arm_atexit((void *)&syscon_key_events, syscon_target_queue_destructor,
                         &syscon_application_dso);
}
uint32_t syscon_target_queue_count(uint32_t address)
{
    volatile syscon_event_queue *queue = (volatile syscon_event_queue *)(uintptr_t)address;
    if (queue->full)
        return queue->capacity;
    uint32_t write = queue->write, read = queue->read;
    if (write >= read) {
        write = queue->write;
        read = queue->read;
        return write - read;
    }
    read = queue->read;
    write = queue->write;
    uint32_t size = queue->capacity;
    return write + size - read;
}
static uint32_t modulo(uint32_t value, uint32_t size)
{
    return size ? value % size : value;
}
void syscon_target_queue_event(uint32_t event)
{
    if (syscon_key_events.full) {
        syscon_target_logger(1, "MAIN", "sPwrKeyEventsBuffer.put(event) failed: %d", UINT32_MAX);
        return;
    }
    uint32_t index = syscon_key_events.write, buffer = syscon_key_events.buffer,
             size = syscon_key_events.capacity;
    B(buffer + index) = (uint8_t)event;
    index = syscon_key_events.write + 1;
    syscon_key_events.write = modulo(index, size);
    index = syscon_key_events.write;
    uint32_t read = syscon_key_events.read;
    if (index == read)
        syscon_key_events.full = 1;
}
void syscon_target_request_off(void)
{
    if (!syscon_target_usb_reattach_request())
        syscon_shutdown_pending = 1;
    else
        syscon_target_modem_poweroff(0);
}
void syscon_target_diagnostic_write(uint32_t data, uint32_t length)
{
    syscon_target_fault_stage_set(17);
    syscon_target_uart_write_buffer(0, data, length);
}
void syscon_target_parser_poll(void)
{
    syscon_target_protocol_poll(ADDRESS(&syscon_console_parser));
}
void syscon_target_log_enable(uint32_t enabled)
{
    syscon_log_enabled = (uint8_t)enabled;
}
void syscon_target_application_gpio_init(void)
{
    uint8_t cfg[12] = {0};
    cfg[5] = 2;
    syscon_target_gpio_config(10, (uint32_t)(uintptr_t)cfg);
    syscon_target_gpio_config(9, (uint32_t)(uintptr_t)cfg);
    syscon_target_gpio_config(24, (uint32_t)(uintptr_t)cfg);
}
void syscon_target_wakeup_irq(uint32_t pin, uint32_t context)
{
    (void)context;
    if (syscon_target_modem_off()) {
        syscon_target_logger(3, "WAKE", "wakeup_isr - check");
        syscon_target_timer_wait_countflags(10);
        if (!syscon_target_gpio_read(pin)) {
            syscon_target_logger(3, "WAKE", "wakeup_isr - check 2");
            syscon_wakeup_pending = 1;
        } else
            syscon_target_logger(3, "WAKE", "wakeup_isr - d fail");
    } else
        syscon_target_logger(3, "WAKE", "wakeup_isr - poff");
}
void syscon_target_wakeup_init(void)
{
    uint8_t cfg[12] = {0};
    syscon_target_gpio_config(17, (uint32_t)(uintptr_t)cfg);
}
void syscon_target_wakeup_enable(uint32_t enabled)
{
    if (enabled && syscon_target_wakeup_enabled()) {
        syscon_target_logger(3, "WAKE", "WAKE pin enabled");
        syscon_target_gpio_attach(17, 2, (uint32_t)(uintptr_t)syscon_target_wakeup_irq, 0);
    } else {
        syscon_target_logger(3, "WAKE", "WAKE pin disabled");
        syscon_target_gpio_detach(17);
    }
}
void syscon_target_wakeup_poll(void)
{
    if (syscon_wakeup_pending) {
        syscon_target_modem_poweron();
        syscon_wakeup_pending = 0;
    }
}

_Noreturn void syscon_target_main(void)
{
    syscon_target_watchdog_init();
    uint32_t previous_stage = syscon_target_fault_stage_get();
    syscon_target_fault_stage_set(1);
    syscon_target_enable_mftick();
    uint8_t uart[9] = {0, 0, 9, 0, 0, 0xc2, 1, 0, 0};
    syscon_target_uart_init(0, (uint32_t)(uintptr_t)uart);
    syscon_target_log_enable(1);
    syscon_target_retained_load();
    syscon_target_timer_init();
    syscon_target_tasks_init();
    syscon_target_watchdog_feed();
    syscon_target_config_init();
    syscon_target_wakeup_init();
    syscon_target_rgb_init(0);
    uint32_t reset = syscon_target_reset_cause();
    if (reset != 1 && reset != 6)
        syscon_target_retained_increment_boots();
    syscon_target_powerkey_init(0);
    syscon_target_powerkey_callback((uint32_t)(uintptr_t)syscon_target_queue_event, 0);
    syscon_target_watchdog_feed();
    int32_t result = syscon_target_ioexpander_init(reset < 2);
    if (result < 0)
        syscon_target_logger(1, "MAIN", "io_expander_init(isPowerOnReset) failed: %d", result);
    syscon_target_logger(3, "MAIN", "******");
    uint32_t reset_name = syscon_target_reset_cause_name(reset);
    uint32_t raw = syscon_target_cached_reason();
    uint32_t stage_name = syscon_target_fault_stage_name(previous_stage);
    syscon_target_logger(3, "MAIN", "* Tachyon SysCon Boot: %s - %s(%d) last:%s",
                         syscon_firmware_version, reset_name, raw, stage_name);
    syscon_target_logger(3, "MAIN", "* Built: %s %s", "Aug 25 2026", "15:29:03");
    uint32_t mode = syscon_target_retained_modem();
    uint32_t mode_name = syscon_target_modem_mode_name(mode);
    uint32_t battery = syscon_target_retained_battery();
    const char *battery_name = syscon_power_name(syscon_power_names.battery, battery);
    uint32_t boots = syscon_target_retained_boots();
    syscon_target_logger(3, "MAIN", "* Retained modem: %s battery: %s reboot: %d", mode_name,
                         battery_name, boots);
    syscon_target_logger(3, "MAIN", "******");
    result = syscon_target_power_policy_init(reset < 2);
    if (result < 0)
        syscon_target_logger(1, "MAIN", "power_manager_init(isPowerOnReset) failed: %d", result);
    mode = syscon_target_retained_modem();
    result = syscon_target_modem_init(mode);
    if (result < 0)
        syscon_target_logger(1, "MAIN", "sg560d_init(mode) failed: %d", result);
    syscon_target_application_gpio_init();
    syscon_target_watchdog_feed();
    if (reset == 1) {
        uint32_t automatic = syscon_target_auto_boot();
        if (syscon_target_demo_enabled())
            syscon_target_rgb_preset(7, 0);
        else if (automatic)
            syscon_target_modem_poweron();
    }
    for (;;) {
        syscon_target_fault_stage_set(2);
        syscon_target_diagnostics_poll();
        syscon_target_fault_stage_set(3);
        if (!syscon_shutdown_pending && syscon_target_queue_count(ADDRESS(&syscon_key_events))) {
            uint32_t event;
            if (!syscon_target_queue_count(ADDRESS(&syscon_key_events))) {
                syscon_target_logger(1, "MAIN", "sPwrKeyEventsBuffer.get(event) failed: %d",
                                     UINT32_MAX);
                event = 255;
            } else {
                uint32_t index = syscon_key_events.read, next = syscon_key_events.read + 1,
                         buffer = syscon_key_events.buffer, size = syscon_key_events.capacity;
                event = B(buffer + index);
                syscon_key_events.read = modulo(next, size);
                syscon_key_events.full = 0;
            }
            if (!syscon_target_demo_enabled()) {
                if (event < 6) {
                    uint32_t old = syscon_key_started_off;
                    static const char *const formats[6] = {
                        "Quick press seen %d", "Quick press confirmed %d",
                        "Short press seen %d", "Short press confirmed %d",
                        "Long press seen %d",  "Long press confirmed %d"};
                    syscon_target_logger(3, "MAIN", formats[event], old);
                    switch (event) {
                    case 0: {
                        uint32_t off = syscon_target_modem_off();
                        syscon_key_started_off = (uint8_t)off;
                        uint32_t fastboot = syscon_target_fastboot_enabled();
                        syscon_target_logger(3, "MAIN", "Power going %s; fastboot %s",
                                             (off ? "on" : "off"), (fastboot ? "enabled" : "disabled"));
                        if (syscon_key_started_off && syscon_target_fastboot_enabled())
                            syscon_target_rgb_key_feedback();
                        break;
                    }
                    case 1:
                        if (syscon_key_started_off)
                            syscon_target_modem_poweron();
                        break;
                    case 2:
                        if (syscon_target_fastboot_enabled())
                            syscon_target_rgb_key_feedback();
                        else if (syscon_key_started_off)
                            syscon_target_modem_edl();
                        else
                            syscon_target_request_off();
                        break;
                    case 3: {
                        uint32_t off = syscon_key_started_off;
                        if (syscon_target_fastboot_enabled()) {
                            if (off)
                                syscon_target_modem_edl();
                            else
                                syscon_target_request_off();
                        }
                        break;
                    }
                    case 4:
                        if (syscon_target_fastboot_enabled() && syscon_key_started_off)
                            syscon_target_rgb_key_feedback();
                        break;
                    case 5:
                        if (syscon_key_started_off && syscon_target_fastboot_enabled())
                            syscon_target_modem_fastboot();
                        break;
                    }
                } else
                    syscon_target_logger(1, "MAIN", "Unknown power key event: %d", event);
            }
        }
        syscon_target_fault_stage_set(4);
        syscon_target_parser_poll();
        syscon_target_fault_stage_set(5);
        syscon_target_modem_poll();
        syscon_target_watchdog_feed();
        syscon_target_fault_stage_set(6);
        syscon_target_tasks_poll();
        syscon_target_fault_stage_set(7);
        if (syscon_shutdown_pending && !syscon_target_tasks_active()) {
            syscon_shutdown_pending = 0;
            syscon_target_modem_poweroff(1);
        }
        syscon_target_fault_stage_set(8);
        syscon_target_wakeup_poll();
    }
}
