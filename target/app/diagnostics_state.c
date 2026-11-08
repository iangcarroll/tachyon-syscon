#include "diagnostics_state.h"

volatile uint8_t syscon_diagnostics_enabled
    __attribute__((section(".data.syscon_diagnostics_enabled"))) = 1;
volatile syscon_diagnostics_state_t syscon_diagnostics_state
    __attribute__((section(".bss.syscon_diagnostics_state")));
