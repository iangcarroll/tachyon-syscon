#ifndef SYSCON_ADC_H
#define SYSCON_ADC_H
#include <stdint.h>
typedef struct {
    uint32_t (*read32)(void *,uint32_t address);
    void (*write32)(void *,uint32_t address,uint32_t value);
    void (*delay_cycles)(void *,uint32_t cycles);
    void (*assertion)(void *,uint32_t line);
    void *ctx;
} syscon_adc_environment;
/* Original entries: 7c54 (init), 7d54 (temperature), 7e7c (raw), 7f24 (millivolts).
 * config contains seven bytes for init; NULL reaches the assertion boundary.
 * UINT64_MAX denotes unsupported entry/assertion, otherwise return low32 bits. */
uint64_t syscon_adc_execute(uint8_t ram[4096],const syscon_adc_environment *,
                           uint32_t entry,uint32_t pin,const uint8_t *config);
#endif
