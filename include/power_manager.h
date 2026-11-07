#ifndef SYSCON_POWER_MANAGER_H
#define SYSCON_POWER_MANAGER_H
#include <stdint.h>
typedef struct {
    uint64_t (*call)(void *,uint32_t,uint32_t,uint32_t,const void *,uint32_t);
    void *ctx;
} syscon_power_environment;
/* GPIO dependencies use this host-only sentinel when the lower layer reset.
 * Ordinary -1 status is not terminal. Clocks retain the entire uint64 range. */
#define SYSCON_POWER_IO_TERMINATED (UINT64_MAX-1)
/* RAM is the original 4 KiB SRAM image. Unsupported/assertion returns UINT64_MAX. */
uint64_t syscon_power_execute(uint8_t *,const syscon_power_environment *,uint32_t,uint32_t);
#endif
