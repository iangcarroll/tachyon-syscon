#ifndef SYSCON_POWER_MANAGER_TARGET_H
#define SYSCON_POWER_MANAGER_TARGET_H
#include <stdint.h>
uint32_t syscon_target_power_measure(uint32_t pin);
uint32_t syscon_target_power_battery_route(void);
uint32_t syscon_target_power_vbus_route(void);
uint32_t syscon_target_power_header_route(void);
uint32_t syscon_target_power_battery_id(void);
uint32_t syscon_target_power_ntc(void);
uint32_t syscon_target_power_boost(void);
uint32_t syscon_target_power_battery_id_set(uint32_t value);
uint32_t syscon_target_power_ntc_set(uint32_t value);
uint32_t syscon_target_power_boost_set(uint32_t value);
uint64_t syscon_target_power_battery_route_set(uint32_t value);
uint64_t syscon_target_power_header_route_set(uint32_t value);
uint32_t syscon_target_power_header_default(void);
uint32_t syscon_target_power_usb_isolate(uint32_t value);
uint64_t syscon_target_power_vbus_route_set(uint32_t value);
uint32_t syscon_target_power_usb_release_callback(void);
uint32_t syscon_target_power_usb_assert_callback(void);
uint32_t syscon_target_power_shutdown_busy(void);
uint32_t syscon_target_power_shutdown_request(void);
uint32_t syscon_target_power_battery_sense_set(uint32_t value);
uint32_t syscon_target_power_battery_detect(void);
#endif
