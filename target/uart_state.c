#include "uart_state.h"

volatile syscon_uart_config_t syscon_uart_config[SYSCON_UART_PORTS]
    __attribute__((section(".bss.syscon_uart_config")));
volatile syscon_uart_ring_t syscon_uart_rings[SYSCON_UART_PORTS]
    __attribute__((section(".bss.syscon_uart_rings")));
