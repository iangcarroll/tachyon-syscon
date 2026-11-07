#include "fault_control.h"
static int reset(const syscon_fault_io *io) {
    io->barrier(io->context);
    io->write(io->context,0xe000ed0c,0x05fa0004);
    /* The original executes another DSB and waits forever until hardware reset.
     * The host contract ends at the reset request, before those instructions. */
    return SYSCON_FAULT_RESET_REQUESTED;
}
int syscon_assertion(const syscon_fault_io *io,const char *file,uint32_t line,const char *expression) {
    io->log_assert(io->context,expression,file,line);
    io->disable_interrupts(io->context);
    uint32_t systick=io->read(io->context,0xe000e010);
    io->write(io->context,0xe000e010,systick&~2u);
    const uint8_t config[12]={0,0,0,0,1,0,0,0,2,0,0,0};
    io->gpio_configure(io->context,2,config);
    io->gpio_configure(io->context,1,config);
    io->gpio_configure(io->context,3,config);
    for (unsigned i=0;i<20;++i) {
        io->gpio_toggle(io->context,3);
        io->delay_cycles(io->context,10000000);
        io->watchdog_feed(io->context);
        if (io->gpio_read(io->context,0)==0) {
            io->delay_cycles(io->context,1600000);
            if (io->gpio_read(io->context,0)==0) return reset(io);
        }
    }
    return reset(io);
}
void syscon_fault_stage_set(const syscon_fault_io *io,uint32_t value) {io->write(io->context,0x400b040c,value);}
unsigned syscon_fault_stage_get(const syscon_fault_io *io) {return io->read(io->context,0x400b040c)&255;}
const char *syscon_fault_stage_name(unsigned value) {
    static const char *const names[]={"NONE","BOOT","DIAG","PWR_KEY","MFG","SG560D","STATE_M","USB_REATT",
        "WAKEUP","I2C_TX_IDLE","I2C_TX_FIFO","I2C_TX_BUSY","I2C_TX_DONE","I2C_RX_IDLE","I2C_RX_BUSY",
        "I2C_RX_FIFO","I2C_RX_DONE","UART_TX","HARD_FAULT","NMI","BAD_IRQ"};
    return value<21 ? names[value] : "BAD";
}
int syscon_fault_hardfault(const syscon_fault_io *io) {syscon_fault_stage_set(io,18);return SYSCON_FAULT_HALTED;}
int syscon_fault_nmi(const syscon_fault_io *io) {syscon_fault_stage_set(io,19);return SYSCON_FAULT_HALTED;}
int syscon_enable_mftick(const syscon_fault_io *io) {
    uint32_t value=io->read(io->context,0x400b0104);
    io->write(io->context,0x400b0104,value|0x1000);
    return 0;
}
unsigned syscon_fault_cached_reason(const uint8_t *value) {return *value;}
