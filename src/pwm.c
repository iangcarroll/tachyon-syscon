#include "pwm.h"
#include <string.h>
_Static_assert(sizeof(syscon_pwm_channel)==12,"PWM mapping ABI");
_Static_assert(sizeof(syscon_pwm_pin)==8,"GPIO mapping ABI");

static void update(const syscon_pwm_io *io,uint32_t address,uint32_t mask,uint32_t value) {
    uint32_t before=io->read(io->context,address);
    io->write(io->context,address,((value^before)&mask)^before);
}
void syscon_pwm_default_board(syscon_pwm_board *board) {
    static const uint8_t pins[25]={12,4,5,6,8,9,23,22,7,14,3,13,21,24,25,15,26,17,10,11,27,0,1,16,18};
    memset(board,0,sizeof(*board));
    for (unsigned i=0;i<3;++i) {
        board->channels[i].pin=(uint8_t)(i+1);
        board->channels[i].mux=2;
        board->channels[i].base=i==0 ? 0x40088000 : 0x40084000;
        board->channels[i].compare=i==1 ? 0 : 1;
    }
    for (unsigned i=0;i<25;++i) {
        board->pins[i].base=0x400a0000;
        board->pins[i].gpio=pins[i];
        board->pins[i].pincm=pins[i];
    }
}
static const syscon_pwm_channel *lookup(const syscon_pwm_board *board,unsigned pin) {
    for (unsigned i=0;i<3;++i) if (board->channels[i].pin==pin) return &board->channels[i];
    return 0;
}
static int fail(const syscon_pwm_io *io,unsigned line) {io->assertion(io->context,line);return -2;}

void syscon_pwm_clock(const syscon_pwm_io *io,uint32_t base,const uint8_t cfg[3]) {
    io->write(io->context,base+0x1008,cfg[0]);
    io->write(io->context,base+0x1000,cfg[1]);
    io->write(io->context,base+0x110c,cfg[2]);
}
void syscon_pwm_compare(const syscon_pwm_io *io,uint32_t base,uint32_t value,unsigned index) {
    io->write(io->context,base+0x1810+index*4,value);
}
void syscon_pwm_capture(const syscon_pwm_io *io,uint32_t base,uint32_t a,uint32_t b,unsigned index) {
    update(io,base+0x1830+index*4,0x27777,a|b);
}
void syscon_pwm_action(const syscon_pwm_io *io,uint32_t base,uint32_t value,unsigned index) {
    update(io,base+0x1870+index*4,0xffc1b6db,value);
}
void syscon_pwm_output(const syscon_pwm_io *io,uint32_t base,uint32_t a,uint32_t b,unsigned index) {
    update(io,base+0x1880+index*4,0x8f,a|b);
}
void syscon_pwm_configure(const syscon_pwm_io *io,uint32_t base,const syscon_pwm_config *cfg) {
    uint32_t action=cfg->mode==0 ? 0x88 : cfg->mode==0x20 ? 0x401 : 0x280;
    if (cfg->extra_channels) {
        syscon_pwm_action(io,base,action,2);syscon_pwm_action(io,base,action,3);
        syscon_pwm_capture(io,base,0,0,2);syscon_pwm_capture(io,base,0,0,3);
        io->write(io->context,base+0x1858,0);io->write(io->context,base+0x185c,0);
        syscon_pwm_output(io,base,0,0,2);syscon_pwm_output(io,base,0,0,3);
    }
    io->write(io->context,base+0x1808,(cfg->mode==0 || cfg->mode==0x20) ? cfg->period-1 : cfg->period>>1);
    syscon_pwm_action(io,base,action,0);syscon_pwm_action(io,base,action,1);
    if (cfg->mode==0x20) update(io,base+0x1804,0x30000000,0x20000000);
    syscon_pwm_capture(io,base,0,0,0);syscon_pwm_capture(io,base,0,0,1);
    io->write(io->context,base+0x1850,0);io->write(io->context,base+0x1854,0);
    syscon_pwm_output(io,base,0,0,0);syscon_pwm_output(io,base,0,0,1);
    update(io,base+0x1804,0x3000ffbf,(uint32_t)cfg->control|cfg->mode|2);
}
int syscon_pwm_init(const syscon_pwm_board *board,const syscon_pwm_io *io,unsigned pin) {
    const syscon_pwm_channel *channel=lookup(board,pin);
    if (!channel) return fail(io,0xd);
    if (pin>=25) return fail(io,0xe);
    const syscon_pwm_pin *gpio=&board->pins[pin];
    io->write(io->context,gpio->base+0x800,0x26000001);
    io->write(io->context,0x40428004+4u*gpio->pincm,(uint32_t)channel->mux|0x80);
    uint32_t base=channel->base;
    if (!(io->read(io->context,base+0x800)&1)) {
        io->write(io->context,base+0x804,0xb1000003);
        io->write(io->context,base+0x800,0x26000001);
        const uint8_t clock[]={2,0,0};
        syscon_pwm_clock(io,base,clock);
        const syscon_pwm_config config={256,0,0,0,0};
        syscon_pwm_configure(io,base,&config);
        io->write(io->context,base+0x1108,1);
        io->write(io->context,base+0x1100,3);
    }
    return 0;
}
int syscon_pwm_write(const syscon_pwm_board *board,const syscon_pwm_io *io,unsigned pin,uint32_t value) {
    const syscon_pwm_channel *channel=lookup(board,pin);
    if (!channel) return fail(io,0x2b);
    update(io,channel->base+0x1804,1,0);
    syscon_pwm_compare(io,channel->base,value,channel->compare);
    update(io,channel->base+0x1804,1,1);
    return 0;
}
