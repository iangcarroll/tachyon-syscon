/* Test-only transport binding. UART bytes execute reconstructed ring/HAL code;
 * clock/color stay explicit test ports. Production uses interface_bindings.c. */
#include "uart_ring_target.h"
void syscon_target_uart_write(unsigned port,const unsigned char *buffer,uint32_t length) {
    if(!port)*(volatile uint32_t *)(uintptr_t)0x400b040cu=17;
    (void)syscon_target_uart_write_buffer(port,(uint32_t)(uintptr_t)buffer,length);
}
void syscon_target_assert(uint32_t file,uint32_t line,uint32_t expression) {
    (void)file;(void)line;(void)expression;__asm__ volatile("bkpt #0");
}
