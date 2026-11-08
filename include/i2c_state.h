#ifndef SYSCON_I2C_STATE_H
#define SYSCON_I2C_STATE_H
#include <stdint.h>

typedef struct {
    uint8_t scl_pin, scl_function, sda_pin, sda_function;
    uint32_t peripheral;
    uint8_t irq, reserved[3];
} syscon_i2c_bus_t;
typedef struct {
    uint8_t error, mode;
} syscon_i2c_state_t;

extern volatile syscon_i2c_bus_t syscon_i2c_bus;
extern volatile syscon_i2c_state_t syscon_i2c_state;
#endif
