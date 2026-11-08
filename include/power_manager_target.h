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
/* Legacy contract: ignores GPIO write errors, returns status 0 without
 * confirming the final route. The log describes the requested transition. */
uint64_t syscon_target_power_battery_route_set(uint32_t value);
uint64_t syscon_target_power_header_route_set(uint32_t value);
uint32_t syscon_target_power_header_default(void);
uint32_t syscon_target_power_usb_isolate(uint32_t value);
uint64_t syscon_target_power_vbus_route_set(uint32_t value);
uint32_t syscon_target_power_usb_release_callback(void);
uint32_t syscon_target_power_usb_assert_callback(void);
/* USB isolation/reattachment, not processor shutdown. Busy includes the
 * 2000 ms cooldown after release; request queues isolation for 250 ms. */
uint32_t syscon_target_usb_reattach_busy(void);
uint32_t syscon_target_usb_reattach_request(void);
/* Zero enables the NTC detection circuit; any nonzero value disables it. */
uint32_t syscon_target_power_ntc_detection_set_disabled(uint32_t disabled);
/* Active probe: at low VBAT, switches the processor battery rail to DC-DC
 * and then NONE; does not restore its previous route or check processor state.
 * Commits the detected battery type and restores the battery NTC source. */
uint32_t syscon_target_power_battery_probe(void);
#endif
