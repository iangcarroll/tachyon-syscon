#include "rgb.h"
#include <string.h>

static const uint8_t presets[10][5] = {
    {255,0,0,20,4}, {255,0,255,30,2}, {180,80,0,80,2},
    {255,255,255,30,2}, {0,255,0,100,2}, {0,255,0,100,1},
    {255,0,255,100,1}, {0,255,255,100,1}, {0,0,0,100,5},
    {255,255,255,50,4}
};
static const uint8_t palette[10][3] = {
    {255,0,0},{255,170,0},{170,255,0},{0,255,85},{0,255,255},
    {0,85,255},{85,0,255},{170,0,255},{255,0,170},{255,0,85}
};

/* The image's soft-float signed conversion saturates out-of-range values.
 * Express the bit behavior explicitly rather than invoking undefined C casts. */
static uint32_t signed_float_conversion(float value) {
    uint32_t bits;
    memcpy(&bits,&value,sizeof(bits));
    unsigned exponent=(bits & 0x7fffffffu)>>23;
    if (exponent<127) return 0;
    if (exponent>=158) return (bits>>31) ? 0x80000000u : 0x7fffffffu;
    uint32_t magnitude=(bits & 0x7fffffu)|0x800000u;
    if (exponent<150) magnitude >>= 150-exponent;
    else magnitude <<= exponent-150;
    return (bits>>31) ? 0u-magnitude : magnitude;
}

static uint32_t unsigned_float_conversion(float value) {
    if (value>=2147483648.0f)
        return signed_float_conversion(value-2147483648.0f)+0x80000000u;
    return signed_float_conversion(value);
}

uint8_t syscon_rgb_scale(const syscon_rgb_state *s,unsigned channel) {
    uint8_t level=(uint8_t)unsigned_float_conversion(s->level);
    uint8_t value=(uint8_t)((channel*(uint32_t)level)/100u);
    return s->active_high ? value : (uint8_t)~value;
}

void syscon_rgb_flush(const syscon_rgb_state *s,const syscon_rgb_io *io) {
    io->pwm_write(io->context,3,syscon_rgb_scale(s,s->red));
    io->pwm_write(io->context,2,syscon_rgb_scale(s,s->green));
    io->pwm_write(io->context,1,syscon_rgb_scale(s,s->blue));
}

int syscon_rgb_init(syscon_rgb_state *s,const syscon_rgb_io *io,unsigned active_high) {
    io->pwm_init(io->context,3);
    io->pwm_init(io->context,2);
    io->pwm_init(io->context,1);
    memset(s,0,20);
    s->active_high=(uint8_t)active_high;
    if (io->timer_register(io->context,20,0,0x5cad,0)<0) io->timer_error(io->context);
    io->timer_init(io->context);
    return 0;
}

int syscon_rgb_brightness(syscon_rgb_state *s,const syscon_rgb_io *io,unsigned value,int flush) {
    if (value>100) value=100;
    s->brightness=(uint8_t)value;
    s->level=(float)value;
    if (flush) syscon_rgb_flush(s,io);
    return 0;
}

int syscon_rgb_pattern(syscon_rgb_state *s,const syscon_rgb_io *io,unsigned value,int flush) {
    if (s->pattern!=value) {
        s->pattern=(uint8_t)value;
        if (value==1) s->increasing=0;
        else if (value==2) s->interval=500;
        else if (value==3) s->interval=100;
        s->ticks=0;
    }
    if (flush) syscon_rgb_flush(s,io);
    return 0;
}

int syscon_rgb_configure(syscon_rgb_state *s,const syscon_rgb_io *io,const uint8_t config[5]) {
    if (!config) return -1;
    s->red=config[0]; s->green=config[1]; s->blue=config[2];
    syscon_rgb_brightness(s,io,config[3],0);
    return syscon_rgb_pattern(s,io,config[4],1);
}

int syscon_rgb_set_state(syscon_rgb_state *s,const syscon_rgb_io *io,unsigned value,uint32_t duration_ms) {
    if (value>=10) return -1;
    s->previous_state=s->state;
    s->state=(uint8_t)value;
    s->duration_ticks=duration_ms/20;
    return syscon_rgb_configure(s,io,presets[value]);
}

void syscon_rgb_tick(syscon_rgb_state *s,const syscon_rgb_io *io) {
    if (s->duration_ticks && --s->duration_ticks==0)
        syscon_rgb_set_state(s,io,s->previous_state,0);
    if (s->pattern==1) {
        float target=(float)s->brightness;
        float step=target/100.0f;
        if (!s->increasing) {
            if (s->level<=step) {s->level=0; s->increasing=1;}
            else s->level=s->level-step;
        } else {
            s->level=s->level+step;
            if (target<=s->level) {s->level=target; s->increasing=0;}
        }
    } else if (s->pattern==2 || s->pattern==3) {
        ++s->ticks;
        if ((unsigned)s->ticks*20<s->interval) return;
        s->ticks=0;
        s->level=s->level==0 ? (float)s->brightness : 0;
    } else if (s->pattern==5) {
        if (++s->ticks<3) return;
        s->ticks=0;
        uint8_t next=(uint8_t)(s->palette_index+1);
        s->palette_index=next<10 ? next : 0;
        s->red=palette[s->palette_index][0];
        s->green=palette[s->palette_index][1];
        s->blue=palette[s->palette_index][2];
    } else return;
    syscon_rgb_flush(s,io);
}

unsigned syscon_rgb_get_state(const syscon_rgb_state *s) {return s->state;}
int syscon_rgb_get_config(const syscon_rgb_state *s,uint8_t config[6]) {
    if (!config) return 0;
    config[0]=s->state; config[1]=s->red; config[2]=s->green;
    config[3]=s->blue; config[4]=s->brightness; config[5]=s->pattern;
    return 1;
}
const char *syscon_rgb_state_name(unsigned value) {
    static const char *const names[]={"off","fastboot","edl","fct","booting","running","connected_wifi","connected_lte","signal","transient"};
    return value<10 ? names[value] : "unknown";
}
const char *syscon_rgb_pattern_name(unsigned value) {
    static const char *const names[]={"off","breathing","blinking","blinking_rapidly","solid","rainbow"};
    return value<6 ? names[value] : "unknown";
}
void syscon_rgb_transient(syscon_rgb_state *s,const syscon_rgb_io *io) {
    syscon_rgb_set_state(s,io,9,40);
}
