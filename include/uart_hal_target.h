#ifndef SYSCON_UART_HAL_TARGET_H
#define SYSCON_UART_HAL_TARGET_H
#include <stdint.h>
uint32_t syscon_target_uart_init(uint32_t port,uint32_t config);
uint32_t syscon_target_uart_deinit(uint32_t port);
void syscon_target_uart_line_config(uint32_t base,uint32_t config);
void syscon_target_uart_clock_config(uint32_t base,uint32_t config);
#endif
