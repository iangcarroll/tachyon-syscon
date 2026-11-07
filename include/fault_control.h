#ifndef SYSCON_FAULT_CONTROL_H
#define SYSCON_FAULT_CONTROL_H
#include <stdint.h>
typedef struct {
    void *context;
    uint32_t (*read)(void *,uint32_t);
    void (*write)(void *,uint32_t,uint32_t);
    void (*log_assert)(void *,const char *expression,const char *file,uint32_t line);
    void (*disable_interrupts)(void *);
    void (*gpio_configure)(void *,unsigned,const uint8_t config[12]);
    void (*gpio_toggle)(void *,unsigned);
    void (*delay_cycles)(void *,uint32_t);
    void (*watchdog_feed)(void *);
    int (*gpio_read)(void *,unsigned);
    void (*barrier)(void *);
} syscon_fault_io;
#define SYSCON_FAULT_RESET_REQUESTED (-1)
#define SYSCON_FAULT_HALTED (-2)
/* Returns only in the host harness, at the original reset or infinite-loop boundary. */
int syscon_assertion(const syscon_fault_io *,const char *file,uint32_t line,const char *expression);
void syscon_fault_stage_set(const syscon_fault_io *,uint32_t);
unsigned syscon_fault_stage_get(const syscon_fault_io *);
const char *syscon_fault_stage_name(unsigned);
int syscon_fault_hardfault(const syscon_fault_io *);
int syscon_fault_nmi(const syscon_fault_io *);
int syscon_enable_mftick(const syscon_fault_io *);
unsigned syscon_fault_cached_reason(const uint8_t *);
#endif
