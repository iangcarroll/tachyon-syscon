#ifndef SYSCON_HAL_HELPERS_H
#define SYSCON_HAL_HELPERS_H
#include <stdint.h>
/* Original 32-bit pointer ABI. These helpers do not validate pointers or indices
 * beyond the checks present in the original image. MMIO is volatile. */
uint32_t syscon_hal_adc_lookup(uint32_t id);
uint32_t syscon_hal_pwm_lookup(uint32_t id);
uint32_t syscon_hal_uart_lookup(uint32_t index);
uint32_t syscon_hal_i2c_lookup(uint32_t index);
void syscon_hal_adc_clock(uint32_t base, uint32_t config);
void syscon_hal_i2c_clock(uint32_t base, uint32_t config);
void syscon_hal_i2c_fill_tx(uint32_t base, uint32_t data, uint32_t count);
void syscon_hal_i2c_flush_tx(uint32_t base);
void syscon_hal_i2c_flush_rx(uint32_t base);
void syscon_hal_uart_put_blocking(uint32_t base, uint32_t value);
void syscon_hal_vref_config(uint32_t base, uint32_t config);
void syscon_hal_vref_clock(uint32_t base, uint32_t config);
#endif
