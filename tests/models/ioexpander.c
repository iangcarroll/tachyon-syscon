#include "ioexpander.h"

static int fail(syscon_io *io, unsigned line) {
    io->assertion(io->context, line);
    return -2;
}

static int write_retry(syscon_io *io, const uint8_t *data, unsigned count, unsigned line) {
    for (unsigned attempt = 0; attempt < 4; ++attempt) {
        int result=io->write(io->context, 0, 0x26, data, count);
        if(result==-2)return -2;
        if(result==(int)count)return 0;
    }
    return fail(io, line);
}

int syscon_io_write16(syscon_io *io, unsigned reg, unsigned value) {
    const uint8_t data[] = {(uint8_t)reg, (uint8_t)value, (uint8_t)(value >> 8)};
    return write_retry(io, data, 3, 0x34);
}

int syscon_io_write8(syscon_io *io, unsigned reg, unsigned value) {
    const uint8_t data[] = {(uint8_t)reg, (uint8_t)value};
    return write_retry(io, data, 2, 0x24);
}

int syscon_io_read8(syscon_io *io, unsigned reg, uint8_t *value) {
    uint8_t address = (uint8_t)reg;
    if (write_retry(io, &address, 1, 0x29)) return -2;
    for (unsigned attempt = 0; attempt < 4; ++attempt) {
        int result=io->read(io->context, 0, 0x26, value, 1);
        if(result==-2)return -2;
        if(result==1)return 0;
    }
    return fail(io, 0x2a);
}

static int write_pin_unchecked(syscon_io *io, unsigned pin, unsigned value) {
    unsigned reg = (pin >> 3) + 2;
    uint8_t mask = (uint8_t)(1u << (pin & 7));
    uint8_t previous;
    if (syscon_io_read8(io, reg, &previous)) return -2;
    if (value == 1) {
        if (previous & mask) return 0;
        previous |= mask;
    } else {
        if (value == 0 && !(previous & mask)) return 0;
        previous &= (uint8_t)~mask;
    }
    return syscon_io_write8(io, reg, previous);
}

int syscon_io_reset(syscon_io *io) {
    if (syscon_io_write16(io, 6, 0xffff)) return -2;
    if (syscon_io_write16(io, 2, 0xffff)) return -2;
    return syscon_io_write16(io, 4, 0);
}

int syscon_io_init(syscon_io *io, unsigned reset_registers) {
    const uint8_t config[8] = {0};
    unsigned attempt;
    for (attempt = 0; attempt < 4; ++attempt) {
        int result=io->init(io->context, 0, config);
        if(result==-2)return -2;
        if(result==0)break;
    }
    if (attempt == 4) return fail(io, 0x5a);
    if (reset_registers && syscon_io_reset(io)) return -2;
    io->initialized = 1;
    return 0;
}

int syscon_io_configure(syscon_io *io, unsigned pin, const syscon_io_config *config) {
    if (!io->initialized) return fail(io, 0x6c);
    if (!config || pin > 15) return fail(io, 0x6d);
    const unsigned reg = (pin >> 3) + 6;
    const uint8_t mask = (uint8_t)(1u << (pin & 7));
    uint8_t previous;
    if (syscon_io_read8(io, reg, &previous)) return -2;
    if (!config->output) {
        if (previous & mask) return 0;
        previous |= mask;
    } else {
        if (config->set_initial_value && write_pin_unchecked(io, pin, config->initial_value)) return -2;
        if (!(previous & mask)) return 0;
        previous &= (uint8_t)~mask;
    }
    if (syscon_io_write8(io, reg, previous)) return -2;
    return syscon_io_read8(io, reg, &previous);
}

int syscon_io_write(syscon_io *io, unsigned pin, unsigned value) {
    if (!io->initialized) return fail(io, 0x8d);
    if (pin > 15) return fail(io, 0x8e);
    uint8_t direction;
    if (syscon_io_read8(io, (pin >> 3) + 6, &direction)) return -2;
    if (direction & (1u << (pin & 7))) {
        io->invalid_output(io->context, pin);
        return -1;
    }
    return write_pin_unchecked(io, pin, value);
}

int syscon_io_read(syscon_io *io, unsigned pin, uint8_t *value) {
    if (!io->initialized) return fail(io, 0x9b);
    if (pin > 15) return fail(io, 0x9c);
    unsigned reg = pin >> 3;
    uint8_t mask = (uint8_t)(1u << (pin & 7));
    uint8_t direction, data;
    if (syscon_io_read8(io, reg + 6, &direction)) return -2;
    if (!(direction & mask)) reg += 2;
    if (syscon_io_read8(io, reg, &data)) return -2;
    *value = (data & mask) != 0;
    return 0;
}

int syscon_gpio_read(syscon_io *io, unsigned pin) {
    if (pin < 25) return io->gpio_read(io->context, pin & 0xffff);
    uint8_t value;
    int result = syscon_io_read(io, (pin - 25) & 0xff, &value);
    return result == -2 ? -2 : result == 0 ? value : -1;
}

int syscon_gpio_write(syscon_io *io, unsigned pin, unsigned value) {
    if (pin < 25) {
        io->gpio_write(io->context, pin & 0xffff, value);
        return 0;
    }
    /* Original wrapper is void and discards expander status. */
    int result = syscon_io_write(io, (pin - 25) & 0xff, value);
    return result == -2 ? -2 : 0;
}
