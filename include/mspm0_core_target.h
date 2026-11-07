#ifndef SYSCON_MSPM0_CORE_TARGET_H
#define SYSCON_MSPM0_CORE_TARGET_H
#include <stdint.h>
void syscon_target_assert(uint32_t file, uint32_t line, uint32_t expression);
uint32_t syscon_target_watchdog_init(void);
uint32_t syscon_target_watchdog_feed(void);
void syscon_target_hal_noop(void);
uint32_t syscon_target_gpio_lookup(uint32_t pin);
uint32_t syscon_target_reset_cause(void);
uint32_t syscon_target_reset_cause_name(uint32_t cause);
uint32_t syscon_target_gpio_config(uint32_t pin, uint32_t config);
uint32_t syscon_target_gpio_write(uint32_t pin, uint32_t value);
uint32_t syscon_target_gpio_toggle(uint32_t pin);
uint32_t syscon_target_gpio_read(uint32_t pin);
/* Original attach entry leaves the input pin in R1 and zero in R0. */
uint64_t syscon_target_gpio_attach(uint32_t pin, uint32_t edge, uint32_t callback, uint32_t context);
uint32_t syscon_target_gpio_detach(uint32_t pin);
void syscon_target_gpio_irq(void);
#endif
