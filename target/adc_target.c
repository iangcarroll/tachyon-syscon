#include "adc_target.h"
#include "hal_helpers.h"
#include "mspm0_core_target.h"
#include "runtime_memory.h"
#include "runtime_arithmetic.h"
#define U8(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))
extern void syscon_cycle_delay(uint32_t);
static void adc_assert(uint32_t line,uint32_t expression) {
    uint32_t file=0xdee4u;
    if(syscon_rt_strrchr((const void *)(uintptr_t)file,'/'))
        file=(uint32_t)(uintptr_t)syscon_rt_strrchr((const void *)(uintptr_t)file,'/')+1u;
    syscon_target_assert(file,line,expression);
}
uint64_t syscon_target_adc_init(uint32_t pin,uint32_t config) {
    uint32_t descriptor=syscon_hal_adc_lookup((uint8_t)pin);
    if(!descriptor)adc_assert(0x15u,0xdf28u);
    if(!config)adc_assert(0x16u,0xdf37u);
    uint32_t base=U32(descriptor+4u);
    U32(base+0x804u)=0xb1000003u;
    U32(base+0x800u)=0x26000001u;
    uint32_t clock[2];clock[0]=U32(0xabe0u);clock[1]=U32(0xabe4u);
    syscon_hal_adc_clock(base,(uint32_t)(uintptr_t)clock);
    base=U32(descriptor+4u);
    uint32_t old=U32(base+0x1104u);
    U32(base+0x1104u)=old^((old^0x100000u)&0x130001u);
    old=U32(base+0x1108u);U32(base+0x1108u)=old&0xe0e0fff8u;
    U32(base+0x1114u)=0x1au;
    old=U32(base+0x1100u);U32(base+0x1100u)=old|0x10000u;
    syscon_rt_memcpy((void *)0x20000685u,(const void *)(uintptr_t)config,7);
    uint32_t high=U8(config+5u),low=U8(config+4u);
    U8(0x2000068du)=(uint8_t)high;
    U8(0x2000068cu)=(uint8_t)low;
    U8(0x2000068eu)=0;U8(0x2000068fu)=0;
    return (uint64_t)clock[0]<<32;
}
uint32_t syscon_target_adc_temperature(void) {
    uint32_t initialized=U8(0x20000694u);
    if(!initialized) {
        U32(0x40030804u)=0xb1000001u;U32(0x40030800u)=0x26000001u;
        uint8_t clock[2]={8,0};
        syscon_hal_vref_clock(0x40030000u,(uint32_t)(uintptr_t)clock);
        union {uint32_t words[3];uint16_t halves[6];} configuration;
        syscon_rt_memset(&configuration,0,12);configuration.halves[0]=0x8001u;
        syscon_hal_vref_config(0x40030000u,(uint32_t)(uintptr_t)&configuration);
        U8(0x20000694u)=1;
    }
    uint32_t remaining=100;
    do {
        if(U32(0x40031104u)&1u)break;
        --remaining;syscon_cycle_delay(320);
    } while(remaining);
    if(!(U32(0x40031104u)&1u))return 0x80000000u;
    uint32_t old=U32(0x40005100u);U32(0x40005100u)=old&~1u;
    U32(0x40005180u)=0x100020bu;
    old=U32(0x40005100u);U32(0x40005100u)=old|1u;
    old=U32(0x40005104u);U32(0x40005104u)=old|0x100u;
    syscon_cycle_delay(32000);
    old=U32(0x40005104u);U32(0x40005104u)=old&~0x100u;
    syscon_cycle_delay(3200);
    uint32_t measured=U32(0x4055a280u)&0xffffu;
    uint32_t access=U32(0x40401300u)&7u;
    U32(0x40401300u)=5;
    uint32_t calibration=U32(0x41c4003cu);
    U32(0x40401300u)=access;
    if(!calibration || calibration==0xfffu)return 0x80000000u;
    uint32_t product=(measured-calibration)*14000u;
    return (uint32_t)syscon_rt_idiv32(product,0xffffe400u)+300u;
}
uint32_t syscon_target_adc_raw(uint32_t pin) {
    uint32_t descriptor=syscon_hal_adc_lookup((uint8_t)pin);
    if(!descriptor)adc_assert(0x83u,0xdf28u);
    uint32_t base=U32(descriptor+4u);
    uint32_t old=U32(base+0x1100u);U32(base+0x1100u)=old&~1u;
    uint32_t channel=U8(descriptor+8u);
    uint32_t slot=U8(descriptor+9u);
    U32(base+0x1180u+slot*4u)=channel|0x1000000u;
    old=U32(base+0x1100u);U32(base+0x1100u)=old|1u;
    old=U32(base+0x1104u);U32(base+0x1104u)=old|0x100u;
    syscon_cycle_delay(32000);
    base=U32(descriptor+4u);old=U32(base+0x1104u);U32(base+0x1104u)=old&~0x100u;
    syscon_cycle_delay(3200);
    slot=U8(descriptor+9u);base=U32(descriptor+4u);
    return U32(base+0x556280u+slot*4u)&0xffffu;
}
uint32_t syscon_target_adc_millivolts(uint32_t pin) {
    uint32_t raw=syscon_target_adc_raw(pin);
    if(raw&0x80000000u)return raw;
    uint32_t high=U8(0x2000068du),low=U8(0x2000068cu),third=U8(0x2000068eu);
    uint32_t fourth=U8(0x2000068fu);
    uint32_t product=raw*(low|(high<<8)|(third<<16)|(fourth<<24));
    /* Defined unsigned reconstruction of signed division by 4096 toward zero. */
    uint32_t rounded=product+((product&0x80000000u)?4095u:0u);
    return (rounded>>12)|((rounded&0x80000000u)?0xfff00000u:0u);
}
