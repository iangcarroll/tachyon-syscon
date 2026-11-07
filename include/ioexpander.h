#ifndef SYSCON_IOEXPANDER_H
#define SYSCON_IOEXPANDER_H
#include <stdint.h>

/* Host-testable reconstruction. Callback boundaries replace the original HAL;
 * this context layout is not the original MCU global-variable ABI. */
typedef struct {
    uint8_t output, initial_value, set_initial_value;
} syscon_io_config;
typedef struct {
    void *context;
    int (*init)(void *, unsigned, const uint8_t[8]);
    int (*write)(void *, unsigned, unsigned, const uint8_t *, unsigned);
    int (*read)(void *, unsigned, unsigned, uint8_t *, unsigned);
    void (*assertion)(void *, unsigned line);
    void (*invalid_output)(void *, unsigned pin);
    int (*gpio_read)(void *, unsigned pin);
    void (*gpio_write)(void *, unsigned pin, unsigned value);
    uint8_t initialized;
} syscon_io;

/* -2 is a host-only assertion sentinel. The original assertion does not return.
 * HAL init/read/write callbacks must propagate -2 for a non-returning fault;
 * ordinary recoverable I2C errors use -1. Terminal faults are never retried. */
int syscon_io_write16(syscon_io *, unsigned reg, unsigned value);
int syscon_io_write8(syscon_io *, unsigned reg, unsigned value);
int syscon_io_read8(syscon_io *, unsigned reg, uint8_t *value);
int syscon_io_reset(syscon_io *);
int syscon_io_init(syscon_io *, unsigned reset_registers);
int syscon_io_configure(syscon_io *, unsigned pin, const syscon_io_config *);
int syscon_io_write(syscon_io *, unsigned pin, unsigned value);
int syscon_io_read(syscon_io *, unsigned pin, uint8_t *value);
int syscon_gpio_read(syscon_io *, unsigned pin);
int syscon_gpio_write(syscon_io *, unsigned pin, unsigned value);
#endif
