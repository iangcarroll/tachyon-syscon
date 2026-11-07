#ifndef SYSCON_UART_H
#define SYSCON_UART_H
#include <stdint.h>
#include <stddef.h>
typedef struct {
    uint8_t data[64];
    uint32_t write_index,read_index;
    uint8_t full,padding[3];
} syscon_uart_ring;
_Static_assert(sizeof(syscon_uart_ring)==76,"UART ring ABI");
typedef struct { syscon_uart_ring ring[2]; uint8_t disabled[2],padding[2]; } syscon_uart;
typedef uint32_t (*syscon_uart_readreg)(void *,uint32_t);
typedef void (*syscon_uart_writereg)(void *,uint32_t,uint32_t);
typedef struct { syscon_uart_readreg read;syscon_uart_writereg write;void *ctx; } syscon_uart_io;
int syscon_uart_available(syscon_uart *,unsigned,const syscon_uart_io *);
int syscon_uart_read(syscon_uart *,unsigned,const syscon_uart_io *);
void syscon_uart_irq(syscon_uart *,uint32_t,const syscon_uart_io *);
int syscon_uart_write(syscon_uart *,unsigned,uint32_t,const syscon_uart_io *);
int syscon_uart_write_buffer(syscon_uart *,unsigned,const uint8_t *,size_t,const syscon_uart_io *);
#endif
