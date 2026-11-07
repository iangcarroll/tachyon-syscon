/* Cortex-M SysTick software state recovered from firmware 1.0.52.
 * Addresses held as uint32_t tokens keep the original slot representation on
 * 64-bit hosts. The dispatcher substitutes for the original indirect BLX.
 */
#include "timers.h"
#include <stddef.h>
#include <string.h>

_Static_assert(sizeof(syscon_timer_slot)==24, "timer slot ABI");
_Static_assert(offsetof(syscon_timers,initialized)==96, "timer initialization ABI");
_Static_assert(offsetof(syscon_timers,ticks)==104, "timer clock ABI");

void syscon_timer_init(syscon_timers *t, syscon_register_read read,
                       syscon_register_write write, void *ctx) {
    if (t->initialized) return;
    write(ctx,0xe000e014,0x7cff);
    uint32_t priority=read(ctx,0xe000ed20);
    write(ctx,0xe000ed20,(priority&0x00ffffff)|0xc0000000);
    write(ctx,0xe000e018,0);
    write(ctx,0xe000e010,7);
    memset(t->slots,0,sizeof(t->slots));
    t->initialized=1;
}

int syscon_timer_register(syscon_timers *t, uint32_t interval, uint8_t once,
                         uint32_t callback, uint32_t argument) {
    unsigned index;
    for(index=0;index<4;++index) if(t->slots[index].callback==callback) break;
    if(index==4) {
        for(index=0;index<4;++index) if(t->slots[index].callback==0) break;
        if(index==4) return -1;
    }
    syscon_timer_slot *s=&t->slots[index];
    s->argument=argument;
    s->callback=callback;
    s->interval=interval;
    s->started=t->ticks;
    s->once=once;
    return 0;
}

void syscon_timer_unregister(syscon_timers *t, uint32_t callback) {
    for(unsigned i=0;i<4;++i) if(t->slots[i].callback==callback) {
        t->slots[i].callback=0;
        t->slots[i].argument=0;
    }
}

void syscon_timer_tick(syscon_timers *t, syscon_timer_call call, void *ctx) {
    ++t->ticks;
    for(unsigned i=0;i<4;++i) {
        syscon_timer_slot *s=&t->slots[i];
        if(s->callback && t->ticks-s->started >= s->interval) {
            call(ctx,s->callback,s->argument);
            /* Re-read after the callback: it can replace/unregister a slot. */
            if(s->once) { s->callback=0; s->argument=0; }
            else s->started=t->ticks;
        }
    }
}

uint64_t syscon_timer_now(const syscon_timers *t) { return t->ticks; }

void syscon_timer_delay(syscon_timers *t, uint32_t milliseconds,
                         syscon_watchdog_feed feed, void *ctx) {
    uint64_t start=t->ticks;
    while(t->ticks-start < milliseconds) feed(ctx);
}

void syscon_timer_wait_countflags(uint32_t count, syscon_register_read read, void *ctx) {
    (void)read(ctx,0xe000e010); /* Original clears an existing COUNTFLAG first. */
    uint32_t elapsed=0;
    while(elapsed!=count) if(read(ctx,0xe000e010)&0x10000) ++elapsed;
}
