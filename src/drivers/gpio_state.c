#include "gpio_state.h"

/* Tachyon logical pin order. Each pin uses the GPIOA port and matching IOMUX
 * index. Logical 0 is the button; 1/2/3 are blue/green/red; 21/22 are I2C SCL/SDA.
 * These are hardware routing values, not addresses of firmware objects. */
#define GPIO_A(pin) {0x400a0000u, pin, pin, 0}
volatile syscon_gpio_pin_t syscon_gpio_pins[SYSCON_GPIO_COUNT]
    __attribute__((section(".data.syscon_gpio_pins"))) = {
        GPIO_A(12), GPIO_A(4),  GPIO_A(5),  GPIO_A(6),  GPIO_A(8),  GPIO_A(9),  GPIO_A(23),
        GPIO_A(22), GPIO_A(7),  GPIO_A(14), GPIO_A(3),  GPIO_A(13), GPIO_A(21), GPIO_A(24),
        GPIO_A(25), GPIO_A(15), GPIO_A(26), GPIO_A(17), GPIO_A(10), GPIO_A(11), GPIO_A(27),
        GPIO_A(0),  GPIO_A(1),  GPIO_A(16), GPIO_A(18),
};

volatile syscon_gpio_handler_t syscon_gpio_handlers[SYSCON_GPIO_COUNT]
    __attribute__((section(".bss.syscon_gpio_handlers")));

/* 255 means the reset-cause register has not been sampled since C startup. */
volatile uint8_t syscon_reset_cause_cache
    __attribute__((section(".data.syscon_reset_cause_cache"))) = UINT8_MAX;
