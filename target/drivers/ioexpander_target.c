#include "ioexpander_target.h"
#include "i2c_target.h"
#include "mspm0_core_target.h"
#include "logger_target.h"
#include "runtime_memory.h"
volatile uint8_t syscon_ioexpander_initialized
    __attribute__((section(".bss.syscon_ioexpander_initialized")));
#define POINTER(p) ((uint32_t)(uintptr_t)(p))
static void io_assert(uint32_t line, const char *expression)
{
    syscon_target_assert(POINTER("io_expander.cpp"), line, POINTER(expression));
}
static void transmit(const uint8_t *data, uint32_t count, uint32_t line, const char *expression)
{
    unsigned remaining = 4;
    do {
        if (syscon_target_i2c_transmit(0, 0x26, POINTER(data), count) == count)
            return;
    } while (--remaining);
    io_assert(line, expression);
}
uint32_t syscon_target_ioexpander_write16(uint32_t reg, uint32_t value)
{
    uint8_t data[3] = {(uint8_t)reg, (uint8_t)value, (uint8_t)(value >> 8)};
    transmit(data, 3, 0x34, "hal_i2c_write_to(HAL_I2C_0, IO_EXPANDER_ADDR, buf, 3) == 3");
    return reg;
}
uint32_t syscon_target_ioexpander_write8(uint32_t reg, uint32_t value)
{
    uint8_t data[2] = {(uint8_t)reg, (uint8_t)value};
    transmit(data, 2, 0x24, "hal_i2c_write_to(HAL_I2C_0, IO_EXPANDER_ADDR, buf, 2) == 2");
    return reg;
}
uint32_t syscon_target_ioexpander_read8(uint32_t reg, uint8_t *value)
{
    uint8_t address = (uint8_t)reg;
    transmit(&address, 1, 0x29, "hal_i2c_write_to(HAL_I2C_0, IO_EXPANDER_ADDR, &reg, 1) == 1");
    unsigned remaining = 4;
    do {
        if ((uint32_t)syscon_target_i2c_receive(0, 0x26, POINTER(value), 1) == 1)
            return reg;
    } while (--remaining);
    io_assert(0x2a, "hal_i2c_read_from(HAL_I2C_0, IO_EXPANDER_ADDR, data, 1) == 1");
    return reg;
}
int syscon_target_ioexpander_write_unchecked(uint32_t pin, uint32_t value)
{
    uint32_t reg = (pin >> 3) + 2;
    uint8_t mask = (uint8_t)(1u << (pin & 7)), previous;
    (void)syscon_target_ioexpander_read8(reg, &previous);
    if (value == 1) {
        if (previous & mask)
            return 0;
        previous |= mask;
    } else {
        if (!value && !(previous & mask))
            return 0;
        previous &= (uint8_t)~mask;
    }
    (void)syscon_target_ioexpander_write8(reg, previous);
    return 0;
}
uint32_t syscon_target_ioexpander_reset(void)
{
    (void)syscon_target_ioexpander_write16(6, 0xffff);
    (void)syscon_target_ioexpander_write16(2, 0xffff);
    return syscon_target_ioexpander_write16(4, 0);
}
int syscon_target_ioexpander_init(uint32_t cold)
{
    uint8_t configuration[8];
    syscon_rt_memset(configuration, 0, 8);
    unsigned remaining = 4;
    do {
        if ((uint32_t)syscon_target_i2c_init(0, POINTER(configuration)) == 0)
            break;
    } while (--remaining);
    if (!remaining)
        io_assert(0x5a, "hal_i2c_init(HAL_I2C_0, &config) == 0");
    if (cold)
        (void)syscon_target_ioexpander_reset();
    syscon_ioexpander_initialized = 1;
    return 0;
}
int syscon_target_ioexpander_configure(uint32_t pin, const syscon_io_config *configuration)
{
    if (!syscon_ioexpander_initialized)
        io_assert(0x6c, "sInitialized");
    if (!configuration || pin > 15)
        io_assert(0x6d, "(config != nullptr) && (pin < IO_EXPANDER_TOTAL_PINS)");
    const volatile syscon_io_config *config = configuration;
    uint32_t reg = (pin >> 3) + 6;
    uint8_t mask = (uint8_t)(1u << (pin & 7)), previous;
    (void)syscon_target_ioexpander_read8(reg, &previous);
    if (!config->output) {
        if (previous & mask)
            return 0;
        previous |= mask;
    } else {
        if (config->set_initial_value)
            (void)syscon_target_ioexpander_write_unchecked(pin, config->initial_value);
        if (!(previous & mask))
            return 0;
        previous &= (uint8_t)~mask;
    }
    (void)syscon_target_ioexpander_write8(reg, previous);
    (void)syscon_target_ioexpander_read8(reg, &previous);
    return 0;
}
int syscon_target_ioexpander_write(uint32_t pin, uint32_t value)
{
    if (!syscon_ioexpander_initialized)
        io_assert(0x8d, "sInitialized");
    if (pin > 15)
        io_assert(0x8e, "pin < IO_EXPANDER_TOTAL_PINS");
    uint8_t direction;
    (void)syscon_target_ioexpander_read8((pin >> 3) + 6, &direction);
    if (direction & (1u << (pin & 7))) {
        syscon_target_logger(1, "IOEX", "IOExpander[P%d]: input, invalid op", pin);
        return -1;
    }
    return syscon_target_ioexpander_write_unchecked(pin, value);
}
int syscon_target_ioexpander_read(uint32_t pin, uint8_t *value)
{
    if (!syscon_ioexpander_initialized)
        io_assert(0x9b, "sInitialized");
    if (pin > 15)
        io_assert(0x9c, "pin < IO_EXPANDER_TOTAL_PINS");
    uint32_t reg = pin >> 3;
    uint8_t mask = (uint8_t)(1u << (pin & 7)), direction, data;
    (void)syscon_target_ioexpander_read8(reg + 6, &direction);
    if (!(direction & mask))
        reg += 2;
    (void)syscon_target_ioexpander_read8(reg, &data);
    *value = (data & mask) != 0;
    return 0;
}
uint32_t syscon_target_pin_read(uint32_t pin)
{
    if (pin < 25)
        return syscon_target_gpio_read((uint16_t)pin);
    uint8_t value = 0;
    int result = syscon_target_ioexpander_read((uint8_t)(pin - 25), &value);
    return result ? UINT32_MAX : value;
}
uint32_t syscon_target_pin_write(uint32_t pin, uint32_t value)
{
    if (pin < 25)
        return syscon_target_gpio_write((uint16_t)pin, value);
    return (uint32_t)syscon_target_ioexpander_write((uint8_t)(pin - 25), value);
}
