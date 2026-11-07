#include "uart_hal.h"
#include <string.h>
_Static_assert(sizeof(syscon_uart_hal_port)==16,"UART mapping ABI");

static uint32_t word(const uint8_t *p) {return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static uint32_t half(const uint8_t *p) {return (uint32_t)p[0]|(uint32_t)p[1]<<8;}
static void update(const syscon_uart_hal_io *io,uint32_t address,uint32_t mask,uint32_t value) {
    uint32_t previous=io->read(io->context,address);
    io->write(io->context,address,((value^previous)&mask)^previous);
}
void syscon_uart_hal_default_board(syscon_uart_hal_board *board) {
    const syscon_uart_hal_port ports[2]={
        {4,2,1,5,2,1,{0,0},0x40108000,15,{0,0,0}},
        {6,6,1,7,6,1,{0,0},0x40100000,13,{0,0,0}}};
    syscon_pwm_board pwm;
    syscon_pwm_default_board(&pwm);
    memcpy(board->ports,ports,sizeof(ports));
    memcpy(board->pins,pwm.pins,sizeof(board->pins));
}
void syscon_uart_hal_clock(const syscon_uart_hal_io *io,uint32_t base,const uint8_t config[2]) {
    io->write(io->context,base+0x1008,config[0]);
    io->write(io->context,base+0x1000,config[1]);
}
void syscon_uart_hal_configure(const syscon_uart_hal_io *io,uint32_t base,const uint8_t config[10]) {
    update(io,base+0x1100,1,0);
    update(io,base+0x1100,0x26718,half(config)|config[2]|half(config+4));
    update(io,base+0x1104,0x7e,(uint32_t)config[6]|config[7]|config[8]);
}
static int fail(const syscon_uart_hal_io *io,unsigned line) {io->assertion(io->context,line);return -2;}
void syscon_uart_hal_mask(const syscon_uart_hal_board *board,const syscon_uart_hal_io *io,unsigned index) {
    update(io,board->ports[index].base+0x1028,0x400,0);
}
void syscon_uart_hal_unmask(const syscon_uart_hal_board *board,const syscon_uart_hal_io *io,unsigned index) {
    update(io,board->ports[index].base+0x1028,0x400,0x400);
}
int syscon_uart_hal_init(syscon_uart_hal_state *state,syscon_uart *uart,const syscon_uart_hal_board *board,
                         const syscon_uart_hal_io *io,unsigned index,const uint8_t config[9]) {
    if (index>=2) return fail(io,0x5b);
    if (!config) return fail(io,0x5c);
    const syscon_uart_hal_port *port=&board->ports[index];
    const syscon_pwm_pin *tx=&board->pins[port->tx_pin],*rx=&board->pins[port->rx_pin];
    io->write(io->context,0x40428004+4u*tx->pincm,(uint32_t)port->tx_mux|0x80);
    io->write(io->context,0x40428004+4u*rx->pincm,(uint32_t)port->rx_mux|0x40080);
    uint32_t base=port->base;
    io->write(io->context,base+0x804,0xb1000003);
    io->write(io->context,base+0x800,0x26000001);
    const uint8_t clock[]={8,0};
    syscon_uart_hal_clock(io,base,clock);
    const uint8_t line[10]={0,0,0x18,0,0,0,0,0x30,0,0};
    syscon_uart_hal_configure(io,base,line);
    update(io,base+0x1100,0x18000,0);
    uint32_t baud=word(config+4);
    /* The image performs INTEGER division before converting to float. Its
     * divide-by-zero helper returns zero. All resulting fractional bits are
     * zero, including the very-low-baud 16-bit integer truncation cases. */
    uint32_t quotient=baud ? 2000000u/baud : 0;
    update(io,base+0x1110,0xffff,quotient&0xffff);
    update(io,base+0x1114,0x3f,0);
    /* Preserve two separate volatile reads from the original read/modify/write. */
    uint32_t first=io->read(io->context,base+0x1104);
    uint32_t second=io->read(io->context,base+0x1104);
    io->write(io->context,base+0x1104,(first&1)|(second&~1u));
    if (config[8]==0) {
        update(io,base+0x1028,0x400,0x400);
        if (port->irq>=0) {
            uint32_t mask=1u<<((unsigned)port->irq&31);
            io->write(io->context,0xe000e280,mask);
            io->write(io->context,0xe000e100,mask);
        }
    }
    update(io,base+0x1100,1,1);
    uint32_t count=half(config+2);
    if (count>8) count=9;
    memcpy(state->config[index],config,count);
    uart->disabled[index]=state->config[index][8];
    memset(&uart->ring[index],0,sizeof(uart->ring[index]));
    return 0;
}
int syscon_uart_hal_deinit(const syscon_uart_hal_board *board,const syscon_uart_hal_io *io,unsigned index) {
    if (index>=2) return fail(io,0x96);
    const syscon_uart_hal_port *port=&board->ports[index];
    uint32_t mask=1u<<((unsigned)(uint8_t)port->irq&31);
    if (port->irq>=0) io->write(io->context,0xe000e180,mask);
    uint32_t base=port->base;
    update(io,base+0x1028,0x400,0);
    if (port->irq>=0) io->write(io->context,0xe000e280,mask);
    update(io,base+0x1100,1,0);
    io->write(io->context,base+0x804,0xb1000003);
    io->write(io->context,base+0x800,0x26000000);
    const syscon_pwm_pin *tx=&board->pins[port->tx_pin],*rx=&board->pins[port->rx_pin];
    io->write(io->context,0x40428004+4u*tx->pincm,(uint32_t)port->tx_idle|0x80);
    io->write(io->context,0x40428004+4u*rx->pincm,(uint32_t)port->rx_idle|0x40080);
    return 0;
}
