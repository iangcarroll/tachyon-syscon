#ifndef SYSCON_UART_STATE_H
#define SYSCON_UART_STATE_H
#include <stdint.h>

enum { SYSCON_UART_PORTS = 2, SYSCON_UART_RX_CAPACITY = 64 };
_Static_assert(SYSCON_UART_RX_CAPACITY &&
                   !(SYSCON_UART_RX_CAPACITY & (SYSCON_UART_RX_CAPACITY - 1)),
               "UART receive capacity must be a power of two");
typedef struct {
    uint8_t tx_pin, tx_function, tx_idle_function;
    uint8_t rx_pin, rx_function, rx_idle_function;
    uint8_t reserved0[2];
    uint32_t peripheral;
    uint8_t irq, reserved1[3];
} syscon_uart_port_t;
typedef struct {
    uint8_t header[2], size_le[2], baud_le[4], mode;
} syscon_uart_config_t;
typedef struct {
    uint8_t data[SYSCON_UART_RX_CAPACITY];
    uint32_t write_index, read_index;
    uint8_t full, reserved[3];
} syscon_uart_ring_t;

extern volatile syscon_uart_port_t syscon_uart_ports[SYSCON_UART_PORTS];
extern volatile syscon_uart_config_t syscon_uart_config[SYSCON_UART_PORTS];
extern volatile syscon_uart_ring_t syscon_uart_rings[SYSCON_UART_PORTS];
#endif
