#ifndef SYSCON_MODEL_MEMORY_H
#define SYSCON_MODEL_MEMORY_H

#include <stdint.h>
#include <string.h>

/* Host-side test models store SRAM as bytes. memcpy preserves their native
 * integer representation while allowing unaligned offsets without aliasing
 * violations. These accessors are not part of the physical firmware image. */
static inline uint32_t model_read_u32(const uint8_t *state, unsigned offset)
{
    uint32_t value;
    memcpy(&value, state + offset, sizeof(value));
    return value;
}

static inline uint64_t model_read_u64(const uint8_t *state, unsigned offset)
{
    uint64_t value;
    memcpy(&value, state + offset, sizeof(value));
    return value;
}

static inline void model_write_u32(uint8_t *state, unsigned offset, uint32_t value)
{
    memcpy(state + offset, &value, sizeof(value));
}

static inline void model_write_u64(uint8_t *state, unsigned offset, uint64_t value)
{
    memcpy(state + offset, &value, sizeof(value));
}

#endif
