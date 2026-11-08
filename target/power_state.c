#include "power_state.h"
#include <limits.h>

volatile int32_t syscon_minimum_vph_mv __attribute__((section(".data.syscon_minimum_vph_mv"))) =
    INT32_MAX;
volatile uint8_t syscon_shutdown_reason __attribute__((section(".bss.syscon_shutdown_reason")));
volatile syscon_usb_reattach_state_t syscon_usb_reattach_state
    __attribute__((section(".bss.syscon_usb_reattach_state")));
volatile syscon_shutdown_state_t syscon_shutdown_state
    __attribute__((section(".bss.syscon_shutdown_state")));

syscon_power_names_t syscon_power_names __attribute__((section(".data.syscon_power_names"))) = {
    .header = {"DISCONNECTED", "INPUT", "OUTPUT"},
    .battery = {"UNKNOWN", "PRESENT", "NOT_PRESENT"},
    .battery_route = {"NONE", "BATTERY", "DC-DC"},
    .vbus_route = {"DISCONNECTED", "USB", "5V"},
    .ntc = {"BATTERY", "CONSTANT_RESISTOR"},
    .shutdown = {"UNKNOWN", "REBOOT", "POWEROFF", "BATTERY_LOW", "THERMAL_HIGH", "THERMAL_LOW",
                 "BROWNOUT"},
};
