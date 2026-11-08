#include "config_state.h"

/* Ordinary initialized data: reset copies the linker-selected load image. */
__attribute__((section(".data.syscon_config_state"))) syscon_configuration_state
    syscon_config_state = {.edl_timer_le = {3}, .shutdown_timer_le = {3}};
