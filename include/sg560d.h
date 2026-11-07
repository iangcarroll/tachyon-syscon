#ifndef SYSCON_SG560D_H
#define SYSCON_SG560D_H
#include <stddef.h>
#include <stdint.h>

/* Explicit dependency adapter. Arguments retain original 32-bit values;
 * pointer payloads (task lists) are passed separately for native host tests. */
typedef uint64_t (*sg560d_dependency)(void *ctx,uint32_t entry,uint32_t a0,
    uint32_t a1,uint32_t a2,uint32_t a3,const void *payload,size_t length);
typedef struct { sg560d_dependency call; void *ctx; } sg560d_environment;

/* RAM uses offsets from 0x20000000. Only recovered globals are changed.
 * This is a host-test ABI; it is not a replacement binary entry point. */
uint64_t sg560d_execute(uint8_t ram[4096],const sg560d_environment *,
                       uint32_t entry,uint32_t a0,uint32_t a1);
#endif
