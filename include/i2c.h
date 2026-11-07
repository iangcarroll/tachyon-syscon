#ifndef SYSCON_I2C_H
#define SYSCON_I2C_H
#include <stdint.h>
typedef struct {
    uint32_t (*read32)(void *,uint32_t address);
    void (*write32)(void *,uint32_t address,uint32_t value);
    void (*delay_cycles)(void *,uint32_t cycles);
    void (*assertion)(void *,uint32_t line);
    void *ctx;
} syscon_i2c_environment;
/* init82f0: data=config8; write844c/read860c: data=buffer, length=count.
 * error82b4: address=reason; IRQ8798 ignores arguments. Bus0 only.
 * Returns UINT64_MAX at unsupported/assertion boundary; original returns low32.
 * As in the original, length>=256 may fail to progress and flush loops may hang. */
uint64_t syscon_i2c_execute(uint8_t ram[4096],const syscon_i2c_environment *,
    uint32_t entry,uint32_t bus,uint32_t address,uint8_t *data,uint32_t length);
#endif
