#ifndef SYSCON_UART_HAL_H
#define SYSCON_UART_HAL_H
#include "uart.h"
#include "pwm.h"
typedef struct {
    uint8_t tx_pin,tx_mux,tx_idle,rx_pin,rx_mux,rx_idle,pad0[2];
    uint32_t base;
    int8_t irq;
    uint8_t pad1[3];
} syscon_uart_hal_port;
typedef struct {syscon_uart_hal_port ports[2];syscon_pwm_pin pins[25];} syscon_uart_hal_board;
typedef struct {uint8_t config[2][9];} syscon_uart_hal_state;
typedef syscon_pwm_io syscon_uart_hal_io;
void syscon_uart_hal_default_board(syscon_uart_hal_board *);
int syscon_uart_hal_init(syscon_uart_hal_state *,syscon_uart *,const syscon_uart_hal_board *,const syscon_uart_hal_io *,unsigned,const uint8_t config[9]);
int syscon_uart_hal_deinit(const syscon_uart_hal_board *,const syscon_uart_hal_io *,unsigned);
/* Original mask/unmask entries assume a valid port; index < 2 is required. */
void syscon_uart_hal_mask(const syscon_uart_hal_board *,const syscon_uart_hal_io *,unsigned);
void syscon_uart_hal_unmask(const syscon_uart_hal_board *,const syscon_uart_hal_io *,unsigned);
void syscon_uart_hal_clock(const syscon_uart_hal_io *,uint32_t base,const uint8_t config[2]);
void syscon_uart_hal_configure(const syscon_uart_hal_io *,uint32_t base,const uint8_t config[10]);
#endif
