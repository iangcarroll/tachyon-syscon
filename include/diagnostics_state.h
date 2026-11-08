#ifndef SYSCON_DIAGNOSTICS_STATE_H
#define SYSCON_DIAGNOSTICS_STATE_H
#include <stdint.h>

typedef struct {
    uint32_t loops_low, loops_high;
    uint32_t last_check_ms;
    uint32_t last_rate_ms;
} syscon_diagnostics_state_t;

extern volatile uint8_t syscon_diagnostics_enabled;
extern volatile syscon_diagnostics_state_t syscon_diagnostics_state;
#endif
