#ifndef SYSCON_I2C_TARGET_H
#define SYSCON_I2C_TARGET_H
#include <stdint.h>
uint32_t syscon_target_i2c_error(uint32_t descriptor,uint32_t stage);
uint64_t syscon_target_i2c_init(uint32_t bus,uint32_t config);
uint32_t syscon_target_i2c_transmit(uint32_t bus,uint32_t address,uint32_t data,uint32_t count);
uint64_t syscon_target_i2c_receive(uint32_t bus,uint32_t address,uint32_t data,uint32_t count);
void syscon_target_i2c_irq(void);
#endif
