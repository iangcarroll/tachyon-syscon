#ifndef SYSCON_TIMERS_H
#define SYSCON_TIMERS_H
#include <stdint.h>

typedef struct {
    uint64_t started;
    uint32_t interval;
    uint8_t once;
    uint8_t reserved[3];
    uint32_t callback;
    uint32_t argument;
} syscon_timer_slot;

typedef struct {
    syscon_timer_slot slots[4];
    uint8_t initialized;
    uint8_t reserved[7];
    uint64_t ticks;
} syscon_timers;

typedef void (*syscon_timer_call)(void *ctx, uint32_t callback, uint32_t argument);
typedef uint32_t (*syscon_register_read)(void *ctx, uint32_t address);
typedef void (*syscon_register_write)(void *ctx, uint32_t address, uint32_t value);
typedef void (*syscon_watchdog_feed)(void *ctx);

void syscon_timer_init(syscon_timers *, syscon_register_read, syscon_register_write, void *);
int syscon_timer_register(syscon_timers *, uint32_t interval, uint8_t once, uint32_t callback, uint32_t argument);
void syscon_timer_unregister(syscon_timers *, uint32_t callback);
void syscon_timer_tick(syscon_timers *, syscon_timer_call, void *);
uint64_t syscon_timer_now(const syscon_timers *);
void syscon_timer_delay(syscon_timers *, uint32_t, syscon_watchdog_feed, void *);
void syscon_timer_wait_countflags(uint32_t, syscon_register_read, void *);

typedef struct { uint8_t magic, modes, boots; } syscon_retained;
void syscon_retained_load(syscon_retained *, syscon_register_read, syscon_register_write, void *);
void syscon_retained_commit(const syscon_retained *, syscon_register_write, void *);
void syscon_retained_clear_registers(syscon_register_write, void *);
void syscon_retained_set_modem(syscon_retained *, uint8_t, syscon_register_write, void *);
void syscon_retained_set_battery(syscon_retained *, uint8_t, syscon_register_write, void *);
void syscon_retained_increment_boots(syscon_retained *, syscon_register_write, void *);
uint8_t syscon_retained_modem(const syscon_retained *);
uint8_t syscon_retained_battery(const syscon_retained *);
uint8_t syscon_retained_boots(const syscon_retained *);
#endif
