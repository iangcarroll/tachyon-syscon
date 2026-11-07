#ifndef SYSCON_POWER_POLICY_H
#define SYSCON_POWER_POLICY_H
#include <stdint.h>
typedef struct {
    uint64_t (*call)(void *, uint32_t address, uint32_t a, uint32_t b,
                     const void *payload, uint32_t size);
    void *ctx;
} syscon_power_policy_environment;
/* Full 4KiB original RAM image. For report output callbacks: a=format ROM
 * address, b=argument count, payload=that many uint32_t printf arguments.
 * ADC and I/O init callbacks receive their exact initialized byte payload.
 * UINT64_MAX means unsupported entry; void original functions return0 here. */
uint64_t syscon_power_policy_execute(uint8_t ram[4096],
    const syscon_power_policy_environment *, uint32_t entry, uint32_t argument);
#endif
