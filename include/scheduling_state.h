#ifndef SYSCON_SCHEDULING_STATE_H
#define SYSCON_SCHEDULING_STATE_H
#include "syscon.h"
#include "timers.h"

/* The clock is deliberately read/written low word then high word. Keeping
 * separate words preserves the original interrupt-visible torn-read behavior. */
typedef struct {
    syscon_timer_slot slots[4];
    uint8_t initialized;
    uint8_t reserved[7];
    uint32_t ticks_low, ticks_high;
} syscon_timer_state_t;
extern volatile syscon_timer_state_t syscon_timer_state;
extern volatile syscon_tasks syscon_task_state;
/* SRAM mirror only; authoritative warm-reset retention lives in PMU scratch. */
extern volatile syscon_retained syscon_retained_state;
#endif
