/* Target-only helpers; exercised exclusively inside the local CPU emulator. */
#include <stdint.h>
extern void syscon_core_log(uint32_t level, const char *tag, const char *message);
void syscon_mcu_sleep(void) {
    volatile uint32_t *const systick = (volatile uint32_t *)(uintptr_t)0xe000e010;
    syscon_core_log(3, (const char *)(uintptr_t)0xdbe7, (const char *)(uintptr_t)0xdbd8);
    __asm__ volatile ("cpsid i" ::: "memory");
    *systick &= ~UINT32_C(2);
    __asm__ volatile ("dsb sy\nisb sy\nwfi\ncpsie i" ::: "memory");
    *systick |= 2;
    syscon_core_log(3, (const char *)(uintptr_t)0xdbe7, (const char *)(uintptr_t)0xdbec);
}
/* Exact instruction shape matters here. Inputs 0/1 underflow into long delays.
 * Physical cycles/second and flash wait states remain unverified. */
__attribute__((naked)) void syscon_cycle_delay(uint32_t cycles __attribute__((unused))) {
    __asm__ volatile ("sub r3, r0, #2\n1: sub r3, #4\nmov r8, r8\nbcs 1b\nbx lr");
}
