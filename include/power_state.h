#ifndef SYSCON_POWER_STATE_H
#define SYSCON_POWER_STATE_H
#include <stdint.h>

/* Split timestamp words preserve the original volatile access order on M0+. */
typedef struct {
    uint8_t active;
    uint8_t reserved[7];
    uint32_t released_low, released_high;
} syscon_usb_reattach_state_t;

typedef struct {
    uint8_t stale;
    uint8_t reserved[7];
    uint32_t started_low, started_high;
} syscon_shutdown_state_t;

extern volatile int32_t syscon_minimum_vph_mv;
extern volatile uint8_t syscon_shutdown_reason;
extern volatile syscon_usb_reattach_state_t syscon_usb_reattach_state;
extern volatile syscon_shutdown_state_t syscon_shutdown_state;

/* Named source strings replace pointers into the original initialized RAM.
 * The arrays remain volatile to retain read order across logging callbacks. */
typedef struct {
    const char *volatile header[3];
    const char *volatile battery[3];
    const char *volatile battery_route[3];
    const char *volatile vbus_route[3];
    const char *volatile ntc[2];
    const char *volatile shutdown[7];
} syscon_power_names_t;
extern syscon_power_names_t syscon_power_names;
_Static_assert(sizeof(syscon_power_names_t) == 84, "ARM32 power-name fixture layout");

/* Full-width indexing retains the target's unsigned index arithmetic. Valid
 * enum values are the public contract; adjacent private bytes are not. */
static inline const char *syscon_power_name(const char *volatile *names, uint32_t index)
{
    return *(const char *volatile *)((uintptr_t)names + (index << 2));
}
#endif
