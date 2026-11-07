#include "pwm_target.h"
#include "hal_helpers.h"
#include "mspm0_core_target.h"
#include "runtime_memory.h"
#define U8(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))
static void pwm_assert(uint32_t line,uint32_t expression) {
    uint32_t file=0xe04cu;
    if(syscon_rt_strrchr((void *)(uintptr_t)file,'/'))
        file=(uint32_t)(uintptr_t)syscon_rt_strrchr((void *)(uintptr_t)file,'/')+1u;
    syscon_target_assert(file,line,expression);
}
void syscon_target_pwm_clock(uint32_t base,uint32_t config) {
    uint32_t v=U8(config);U32(base+0x1008u)=v;
    v=U8(config+1u);U32(base+0x1000u)=v;
    v=U8(config+2u);U32(base+0x110cu)=v;
}
void syscon_target_pwm_compare(uint32_t base,uint32_t value,uint32_t index) {
    U32(base+0x1810u+index*4u)=value;
}
void syscon_target_pwm_capture(uint32_t base,uint32_t a,uint32_t b,uint32_t index) {
    uint32_t address=base+0x1830u+index*4u,old=U32(address);
    U32(address)=old^((old^(a|b))&0x27777u);
}
void syscon_target_pwm_action(uint32_t base,uint32_t value,uint32_t index) {
    uint32_t address=base+0x1870u+index*4u,old=U32(address);
    U32(address)=old^((old^value)&0xffc1b6dbu);
}
void syscon_target_pwm_output(uint32_t base,uint32_t a,uint32_t b,uint32_t index) {
    uint32_t address=base+0x1880u+index*4u,old=U32(address);
    U32(address)=old^((old^(a|b))&0x8fu);
}
uint64_t syscon_target_pwm_configure(uint32_t base,uint32_t config) {
    if(U8(config+5u)) {
        uint32_t mode=U8(config+4u),action=mode==0?0x88u:mode==0x20u?0x401u:0x280u;
        syscon_target_pwm_action(base,action,2);syscon_target_pwm_action(base,action,3);
        syscon_target_pwm_capture(base,0,0,2);syscon_target_pwm_capture(base,0,0,3);
        U32(base+0x1858u)=0;U32(base+0x185cu)=0;
        syscon_target_pwm_output(base,0,0,2);syscon_target_pwm_output(base,0,0,3);
    }
    uint32_t control=U8(config+6u),mode=U8(config+4u),period=U32(config);
    uint32_t action;
    if(mode==0 || mode==0x20u) {U32(base+0x1808u)=period-1u;action=mode?0x401u:0x88u;}
    else {U32(base+0x1808u)=period>>1;action=0x280u;}
    syscon_target_pwm_action(base,action,0);syscon_target_pwm_action(base,action,1);
    if(mode==0x20u) {uint32_t old=U32(base+0x1804u);U32(base+0x1804u)=old^((old^0x20000000u)&0x30000000u);}
    syscon_target_pwm_capture(base,0,0,0);syscon_target_pwm_capture(base,0,0,1);
    U32(base+0x1850u)=0;U32(base+0x1854u)=0;
    syscon_target_pwm_output(base,0,0,0);syscon_target_pwm_output(base,0,0,1);
    uint32_t old=U32(base+0x1804u);U32(base+0x1804u)=old^((old^(control|mode|2u))&0x3000ffbfu);
    return base|((uint64_t)control<<32);
}
uint32_t syscon_target_pwm_init(uint32_t pin) {
    uint32_t pwm=syscon_hal_pwm_lookup(pin),gpio=syscon_target_gpio_lookup(pin);
    if(!pwm)pwm_assert(13u,0xe090u);
    if(!gpio)pwm_assert(14u,0xe09fu);
    uint32_t port=U32(gpio);U32(port+0x800u)=0x26000001u;
    uint32_t function=U8(pwm+1u),mux=U8(gpio+5u);U32(0x40428004u+mux*4u)=function|0x80u;
    uint32_t base=U32(pwm+4u),enabled=U32(base+0x800u);
    if(!(enabled&1u)) {
        U32(base+0x804u)=0xb1000003u;U32(base+0x800u)=0x26000001u;
        uint32_t clock=2;syscon_target_pwm_clock(base,(uint32_t)(uintptr_t)&clock);
        uint32_t config[2]={256,0};base=U32(pwm+4u);syscon_target_pwm_configure(base,(uint32_t)(uintptr_t)config);
        base=U32(pwm+4u);U32(base+0x1108u)=1;U32(base+0x1100u)=3;
    }
    return 0;
}
uint32_t syscon_target_pwm_write(uint32_t pin,uint32_t value) {
    uint32_t pwm=syscon_hal_pwm_lookup(pin);if(!pwm)pwm_assert(0x2bu,0xe090u);
    uint32_t base=U32(pwm+4u),old=U32(base+0x1804u);U32(base+0x1804u)=old&~1u;
    uint32_t index=U8(pwm+8u);syscon_target_pwm_compare(base,value,index);
    base=U32(pwm+4u);old=U32(base+0x1804u);U32(base+0x1804u)=old|1u;
    return 0;
}
