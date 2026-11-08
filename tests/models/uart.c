#include "uart.h"
static const uint32_t bases[2]={0x40108000,0x40100000};
static void rx_interrupt(unsigned port,int enable,const syscon_uart_io *io) {
    uint32_t address=bases[port]+0x1028;
    uint32_t value=io->read(io->ctx,address);
    io->write(io->ctx,address,enable ? value|0x400u:value&~0x400u);
}
int syscon_uart_available(syscon_uart *s,unsigned port,const syscon_uart_io *io) {
    if (port>=2) return -1; /* Original reaches assertion/reset. */
    if (s->disabled[port]) return 0;
    rx_interrupt(port,0,io);
    uint32_t w=s->ring[port].write_index,r=s->ring[port].read_index;
    uint8_t full=s->ring[port].full;
    rx_interrupt(port,1,io);
    if (full) return 64;
    if (w<r) w+=64;
    return (int)(w-r);
}
int syscon_uart_read(syscon_uart *s,unsigned port,const syscon_uart_io *io) {
    if (port>=2) return -1;
    if (s->disabled[port] || syscon_uart_available(s,port,io)<=0) return -1;
    rx_interrupt(port,0,io);
    syscon_uart_ring *r=&s->ring[port];
    uint8_t value=r->data[r->read_index];
    r->read_index=(r->read_index+1u)&63u;r->full=0;
    rx_interrupt(port,1,io);
    return value;
}
void syscon_uart_irq(syscon_uart *s,uint32_t base,const syscon_uart_io *io) {
    unsigned port;
    if (base==bases[1]) port=1;
    else if (base==bases[0]) port=0;
    else return;
    if ((io->read(io->ctx,base+0x1020)&255u)!=11) return;
    uint32_t value=io->read(io->ctx,base+0x1124);
    if (syscon_uart_available(s,port,io)!=64) {
        syscon_uart_ring *r=&s->ring[port];
        r->data[r->write_index]=(uint8_t)value;
        r->write_index=(r->write_index+1u)&63u;
        if (r->write_index==r->read_index) r->full=1;
    }
}
static void put(unsigned port,uint32_t byte,const syscon_uart_io *io) {
    while (io->read(io->ctx,bases[port]+0x1108)&0x80u) {}
    io->write(io->ctx,bases[port]+0x1120,byte);
}
int syscon_uart_write(syscon_uart *s,unsigned port,uint32_t byte,const syscon_uart_io *io) {
    if (port>=2) return -1;
    if (!s->disabled[port]) put(port,byte,io);
    return 0;
}
int syscon_uart_write_buffer(syscon_uart *s,unsigned port,const uint8_t *data,size_t len,const syscon_uart_io *io) {
    if (port>=2) return -1;
    if (!s->disabled[port]) for (size_t i=0;i<len;i++) put(port,data[i],io);
    return 0;
}
