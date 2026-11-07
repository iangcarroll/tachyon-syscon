#ifndef SYSCON_SCHEDULING_TARGET_H
#define SYSCON_SCHEDULING_TARGET_H
#include <stdint.h>
#include "syscon.h"
/* Original ABI: no host context or RAM argument. Fixed firmware 1.0.52 layout. */
void syscon_target_timer_tick(void);                 /* 76f8 */
void syscon_target_timer_init(void);                 /* 776c */
uint64_t syscon_target_now(void);                    /* 77b4 */
void syscon_target_timer_delay(uint32_t milliseconds); /* 77c0 */
void syscon_target_timer_wait_countflags(uint32_t count); /* 77fc */
int syscon_target_timer_register(uint32_t interval,uint32_t once,uint32_t callback,uint32_t argument); /* 781c */
void syscon_target_timer_unregister(uint32_t callback); /* 7880 */
void syscon_target_tasks_init(void);                 /* 7540 */
int syscon_target_tasks_submit(const syscon_action *,uint32_t count); /* 7554 */
void syscon_target_tasks_poll(void);                 /* 75d8 */
int syscon_target_tasks_active(void);                /* 76d8 */
void syscon_target_retained_commit(void);            /* 59a0 */
void syscon_target_retained_load(void);              /* 59d8 */
void syscon_target_retained_clear_registers(void);   /* 5a88 */
void syscon_target_retained_set_modem(uint32_t);     /* 5aa8 */
uint32_t syscon_target_retained_modem(void);         /* 5ac4 */
void syscon_target_retained_set_battery(uint32_t);   /* 5ad4 */
uint32_t syscon_target_retained_battery(void);       /* 5af0 */
void syscon_target_retained_increment_boots(void);  /* 5afc */
uint32_t syscon_target_retained_boots(void);         /* 5b14 */
/* Link dependencies, not implementation hooks. */
void syscon_target_logger(uint32_t,const char *,const char *,...);
uint32_t syscon_target_watchdog_feed(void);
#endif
