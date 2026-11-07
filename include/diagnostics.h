#ifndef SYSCON_DIAGNOSTICS_H
#define SYSCON_DIAGNOSTICS_H
#include <stdint.h>
typedef struct {
    void *ctx;
    uint64_t (*call)(void *,uint32_t,uint32_t);
    void (*log)(void *,uint32_t,const uint32_t *,const char *);
} syscon_diagnostics_io;
void syscon_diagnostics_enable(uint8_t ram[4096],uint32_t);
void syscon_diagnostics_poll(uint8_t ram[4096],const syscon_diagnostics_io *);
uint32_t syscon_runtime_get(const uint8_t ram[4096],uint32_t);
int syscon_hwrevision_new(const char *);
#endif
