#ifndef SYSCON_UART_RING_TARGET_H
#define SYSCON_UART_RING_TARGET_H
#include <stdint.h>
/* Change only the RX interrupt mask. The receiver and FIFO remain enabled. */
void syscon_target_uart_rx_irq_mask(uint32_t port);
void syscon_target_uart_rx_irq_unmask(uint32_t port);
uint32_t syscon_target_uart_put(uint32_t port, uint32_t character);
/* 8c8c: normal return also leaves R1=port, R2=size, R3=size. */
uint32_t syscon_target_uart_write_buffer(uint32_t port, uint32_t data, uint32_t size);
uint32_t syscon_target_uart_available(uint32_t port);
void syscon_target_uart_irq(uint32_t base);
uint32_t syscon_target_uart_read(uint32_t port);
/* Original assertion dependency, implemented separately from this module. */
void syscon_target_assert(uint32_t file, uint32_t line, uint32_t expression);
#endif
