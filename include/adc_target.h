#ifndef SYSCON_ADC_TARGET_H
#define SYSCON_ADC_TARGET_H
#include <stdint.h>
uint64_t syscon_target_adc_init(uint32_t pin,uint32_t config);
uint32_t syscon_target_adc_temperature(void);
uint32_t syscon_target_adc_raw(uint32_t pin);
uint32_t syscon_target_adc_millivolts(uint32_t pin);
#endif
