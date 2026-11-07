#ifndef SYSCON_POWER_KEY_STATE_H
#define SYSCON_POWER_KEY_STATE_H
#include <stdint.h>

/* Press intervals include start_ms and exclude end_ms. Even event numbers are
 * press events; the following odd number is their corresponding release. */
typedef struct {
    uint32_t start_ms, end_ms;
    uint8_t event;
    uint8_t reserved[3];
} syscon_powerkey_range_t;

typedef struct {
    uint8_t mode; /* Zero forwards the button to the modem's power-key input. */
    uint8_t event; /* 255 means no active press. */
} syscon_powerkey_control_t;

typedef struct {
    uint32_t pressed_ms;
    uint32_t callback;
    uint32_t released_ms;
    uint8_t release_pending;
    uint8_t forced;
    uint8_t reserved[2];
    uint32_t context;
    uint16_t pin;
    uint8_t trailing_reserved[2];
} syscon_powerkey_runtime_t;

/* These are ordinary linker-allocated objects. The split preserves access
 * widths/order for differential tests; it is not a physical placement ABI. */
extern volatile syscon_powerkey_range_t syscon_powerkey_ranges[3];
extern volatile syscon_powerkey_control_t syscon_powerkey_control;
extern volatile syscon_powerkey_runtime_t syscon_powerkey_runtime;
#endif
