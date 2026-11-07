#include "i2c_target.h"
#include "hal_helpers.h"
#include "mspm0_core_target.h"
#include "fault_control_target.h"
#include "runtime_memory.h"
#define U8(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))
extern void syscon_cycle_delay(uint32_t cycles);
extern void syscon_target_logger(uint32_t level,const char *module,const char *format,...);
static void i2c_assert(uint32_t line,uint32_t expression) {
    uint32_t file=0xdfbeu;
    if(syscon_rt_strrchr((void *)(uintptr_t)file,'/'))
        file=(uint32_t)(uintptr_t)syscon_rt_strrchr((void *)(uintptr_t)file,'/')+1u;
    syscon_target_assert(file,line,expression);
}
uint32_t syscon_target_i2c_error(uint32_t descriptor,uint32_t stage) {
    uint32_t name=syscon_target_fault_stage_name(stage);
    syscon_target_logger(1,(const char *)0xdfb9u,(const char *)0xdfa9u,name);
    uint32_t base=U32(descriptor+4u);U32(base+0x1214u)=0;
    syscon_hal_i2c_flush_tx(base);base=U32(descriptor+4u);syscon_hal_i2c_flush_rx(base);
    return UINT32_MAX;
}
uint64_t syscon_target_i2c_init(uint32_t bus,uint32_t config) {
    uint32_t descriptor=syscon_hal_i2c_lookup(bus);
    if(!descriptor)i2c_assert(0x57u,0xe002u);
    if(!config)i2c_assert(0x58u,0xdf37u);
    uint32_t base=U32(descriptor+4u);U32(base+0x804u)=0xb1000003u;U32(base+0x800u)=0x26000001u;
    syscon_cycle_delay(1000);
    uint32_t scl=syscon_target_gpio_lookup(U8(descriptor)),sda=syscon_target_gpio_lookup(U8(descriptor+2u));
    uint32_t mux=U8(scl+5u),fn=U8(descriptor+1u),sc=0x40428004u+mux*4u;
    U32(sc)=fn|0xc0080u;
    fn=U8(descriptor+3u);mux=U8(sda+5u);base=U32(descriptor+4u);
    uint32_t sd=0x40428004u+mux*4u;U32(sd)=fn|0xc0080u;
    uint32_t old=U32(sc);U32(sc)=old|0x2000000u;old=U32(sd);U32(sd)=old|0x2000000u;
    uint8_t clock[2]={8,0};syscon_hal_i2c_clock(base,(uint32_t)(uintptr_t)clock);
    base=U32(descriptor+4u);U32(base+0x1224u)=7;
    old=U32(base+0x1200u);U32(base+0x1200u)=old|0x600u;
    old=U32(base+0x1200u);U32(base+0x1200u)=old|0x100u;
    U32(base+0x1214u)=0;old=U32(base+0x1228u);U32(base+0x1228u)=old|4u;
    if(!U8(config)) {
        U8(0x20000761u)=0;old=U32(base+0x1028u);U32(base+0x1028u)=old|0x480u;
        old=U32(base+0x1228u);U32(base+0x1228u)=old|1u;
    }
    uint32_t irq=U8(descriptor+8u);if(irq<128u) {uint32_t mask=1u<<(irq&31u);U32(0xe000e280u)=mask;U32(0xe000e100u)=mask;}
    return (uint64_t)bus<<32;
}
static uint32_t wait_status(uint32_t descriptor,uint32_t mask,uint32_t wanted,uint32_t *captured) {
    for(uint32_t n=0;n<10000u;n++) {
        uint32_t base=U32(descriptor+4u),status=U32(base+0x1218u);
        if((status&mask)==wanted){*captured=base;return 1;}
        syscon_cycle_delay(32);
    }
    return 0;
}
static void begin(uint32_t base,uint32_t address,uint32_t control) {
    uint32_t old=U32(base+0x1210u);U32(base+0x1210u)=old^((old^address)&0x7ffu);
    old=U32(base+0x1214u);U32(base+0x1214u)=old^((old^control)&0x0fff0007u);
}
uint32_t syscon_target_i2c_transmit(uint32_t bus,uint32_t address,uint32_t data,uint32_t count) {
    uint32_t descriptor=syscon_hal_i2c_lookup(bus);
    if(!descriptor)i2c_assert(0x8eu,0xe002u);
    if(U8(0x20000761u))i2c_assert(0x8fu,0xe011u);
    uint32_t captured;syscon_target_fault_stage_set(9);if(!wait_status(descriptor,0x20,0x20,&captured))return syscon_target_i2c_error(descriptor,9);
    uint32_t done=0,empty=0,started=0,result=0;
    while(done<count) {
        syscon_target_fault_stage_set(10);uint32_t base=U32(descriptor+4u),free=(U32(base+0x123cu)>>8)&15u;
        if(free) {
            uint32_t n=count-done;if((n&255u)>free)n=free;n&=255u;
            syscon_hal_i2c_fill_tx(base,data+done,n);done=(done+n)&255u;empty=0;
        } else {
            if(empty>9999u)return syscon_target_i2c_error(descriptor,10);
            syscon_cycle_delay(32);empty++;
        }
        if(!started) {
            base=U32(descriptor+4u);U8(0x20000760u)=0;begin(base,address<<1,(count<<16)|7u);
            syscon_target_fault_stage_set(11);if(!wait_status(descriptor,0x40,0x40,&captured))return syscon_target_i2c_error(descriptor,11);
        }
        started=1;if(U8(0x20000760u)) {syscon_hal_i2c_flush_tx(U32(descriptor+4u));result=UINT32_MAX;break;}
    }
    syscon_target_fault_stage_set(12);uint32_t base;
    if(!wait_status(descriptor,0x40,0,&base))return syscon_target_i2c_error(descriptor,12);
    syscon_hal_i2c_flush_tx(base);return U8(0x20000760u)?result:done;
}
uint64_t syscon_target_i2c_receive(uint32_t bus,uint32_t address,uint32_t data,uint32_t count) {
    uint32_t descriptor=syscon_hal_i2c_lookup(bus),result=0,base,captured;
    if(!descriptor)i2c_assert(0xceu,0xe002u);
    if(U8(0x20000761u))i2c_assert(0xcfu,0xe011u);
    syscon_target_fault_stage_set(13);
    if(!wait_status(descriptor,0x20,0x20,&base)){result=syscon_target_i2c_error(descriptor,13);goto exit;}
    begin(base,(address<<1)|1u,(count<<16)|7u);
    syscon_target_fault_stage_set(14);if(!wait_status(descriptor,0x40,0x40,&captured)){result=syscon_target_i2c_error(descriptor,14);goto exit;}
    for(uint32_t done=0;done<count;done=(done+1u)&255u) {
        syscon_target_fault_stage_set(15);uint32_t n;
        for(n=0;n<10000u;n++) {
            base=U32(descriptor+4u);uint32_t status=U32(base+0x123cu);
            if((status&15u)||U8(0x20000760u))break;
            syscon_cycle_delay(32);
        }
        if(n==10000u){result=syscon_target_i2c_error(descriptor,15);goto exit;}
        if(U8(0x20000760u)){result=UINT32_MAX;break;}
        uint32_t value=U32(base+0x121cu);U8(data+done)=(uint8_t)value;
    }
    syscon_target_fault_stage_set(16);
    if(!wait_status(descriptor,0x40,0,&base)){result=syscon_target_i2c_error(descriptor,16);goto exit;}
    syscon_hal_i2c_flush_rx(base);if(!U8(0x20000760u))result=count;
exit:return ((uint64_t)count<<32)|result;
}
void syscon_target_i2c_irq(void) {
    uint32_t reason=U32(0x400f1020u)&255u;
    if(reason==8u || reason==11u) {
        U8(0x20000760u)=1;syscon_target_logger(1,(const char *)0xdfb9u,(const char *)(uintptr_t)(reason==8u?0xe02eu:0xe037u));
    }
}
