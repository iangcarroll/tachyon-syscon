#ifndef SYSCON_GPIO_STATE_H
#define SYSCON_GPIO_STATE_H
#include <stdint.h>

enum { SYSCON_GPIO_COUNT = 25 };
typedef struct {
    uint32_t port;
    uint8_t physical_pin, mux_index;
    uint16_t reserved;
} syscon_gpio_pin_t;
typedef struct {
    uint32_t callback, context;
} syscon_gpio_handler_t;

/* Board routing and callback registration are separate from MMIO registers. */
extern volatile syscon_gpio_pin_t syscon_gpio_pins[SYSCON_GPIO_COUNT];
extern volatile syscon_gpio_handler_t syscon_gpio_handlers[SYSCON_GPIO_COUNT];
extern volatile uint8_t syscon_reset_cause_cache;
#endif
