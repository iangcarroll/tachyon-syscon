/* Original target fault-control interfaces, including nonreturning reset wait. */
#include "fault_control_target.h"
#include "runtime_memory.h"
#include <stdint.h>
#define U8(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))
extern void syscon_target_logger(uint32_t level, const char *tag, const char *format, ...);
extern uint32_t syscon_target_gpio_config(uint32_t pin, uint32_t config);
extern uint32_t syscon_target_gpio_toggle(uint32_t pin);
extern uint32_t syscon_target_gpio_read(uint32_t pin);
extern uint32_t syscon_target_watchdog_feed(void);
extern void syscon_cycle_delay(uint32_t cycles);

static _Noreturn void request_reset(void) {
    __asm__ volatile("dsb sy" ::: "memory");
    U32(0xe000ed0cu) = 0x05fa0004u;
    __asm__ volatile("dsb sy" ::: "memory");
    for (;;) __asm__ volatile("mov r8,r8");
}
_Noreturn void syscon_target_assert(uint32_t file, uint32_t line, uint32_t expression) {
    syscon_target_logger(1, (const char *)(uintptr_t)0xacf5,
        (const char *)(uintptr_t)0xacc0, expression, file, line, 1u);
    __asm__ volatile("cpsid i" ::: "memory");
    U32(0xe000e010u) = U32(0xe000e010u) & ~2u;
    uint32_t config[3];
    syscon_rt_memset(config, 0, 8);
    ((uint8_t *)config)[4] = 1;
    config[2] = 2;
    syscon_target_gpio_config(2, (uint32_t)(uintptr_t)config);
    syscon_target_gpio_config(1, (uint32_t)(uintptr_t)config);
    syscon_target_gpio_config(3, (uint32_t)(uintptr_t)config);
    uint32_t remaining = 20;
    do {
        syscon_target_gpio_toggle(3);
        syscon_cycle_delay(10000000);
        syscon_target_watchdog_feed();
        if (!syscon_target_gpio_read(0)) {
            syscon_cycle_delay(1600000);
            if (!syscon_target_gpio_read(0)) request_reset();
        }
        remaining = (uint16_t)(remaining - 1u);
    } while (remaining);
    request_reset();
}
void syscon_target_fault_stage_set(uint32_t stage) { U32(0x400b040cu) = stage; }
uint32_t syscon_target_fault_stage_get(void) { return (uint8_t)U32(0x400b040cu); }
uint32_t syscon_target_fault_stage_name(uint32_t stage) {
    return stage <= 20 ? 0xdd7fu + stage*12u : 0xdd7bu;
}
uint32_t syscon_target_enable_mftick(void) {
    U32(0x400b0104u) = U32(0x400b0104u) | 0x1000u;
    return 0;
}
uint32_t syscon_target_cached_reason(void) { return U8(0x20000254u); }
