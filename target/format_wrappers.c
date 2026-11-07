/* Explicit target I/O boundaries for the ARM logger frame adapters.
 * Original-ABI entry bodies now live in logger_target.c/logger_target_abi.S. */
#include <stdint.h>

_Static_assert(sizeof(void *)==4,"ARM32 test ABI required");

__attribute__((noinline,noclone))
void syscon_target_uart_write(unsigned port,const uint8_t *buffer,uint32_t length) {
    (void)port;(void)buffer;(void)length;
    __asm__ volatile("bkpt #0");
}
__attribute__((noinline,noclone))
uint64_t syscon_target_now(void) { __asm__ volatile("bkpt #0");return 0; }
__attribute__((noinline,noclone))
int syscon_target_color(void) { __asm__ volatile("bkpt #0");return 0; }

