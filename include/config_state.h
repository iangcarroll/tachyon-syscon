#ifndef SYSCON_CONFIG_STATE_H
#define SYSCON_CONFIG_STATE_H
#include <stdint.h>

enum syscon_config_flag {
    SYSCON_CONFIG_AUTO_BOOT,
    SYSCON_CONFIG_WAKE_PIN,
    SYSCON_CONFIG_COLOR_DEBUG,
    SYSCON_CONFIG_FASTBOOT,
    SYSCON_CONFIG_DEMO,
    SYSCON_CONFIG_KEEP_5V,
    SYSCON_CONFIG_FLAG_COUNT
};

/* This is an in-memory cache, not the persistent flash format. Byte arrays
 * retain the recovered timer read semantics without unaligned word accesses. */
typedef struct {
    uint8_t flags[SYSCON_CONFIG_FLAG_COUNT];
    uint8_t edl_timer_le[4];
    uint8_t shutdown_timer_le[4];
    char hardware_revision[8];
} syscon_configuration_state;

extern syscon_configuration_state syscon_config_state;
#endif
