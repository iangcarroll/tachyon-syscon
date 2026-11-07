/* Original fixed-RAM report, initialization, voltage minimum and shutdown policy. */
#include "power_policy_target.h"
#include "adc_target.h"
#include "scheduling_target.h"
#include "ioexpander_target.h"
#include "power_manager_target.h"
#include "logger_target.h"
#include <stdint.h>
#define B(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define W(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))
#define S(a) ((const char *)(uintptr_t)(uint32_t)(a))

static uint32_t table(uint32_t base,uint32_t index){return W(base+(index<<2));}
static uint64_t read64(uint32_t address){uint32_t low=W(address),high=W(address+4);return low|((uint64_t)high<<32);}
static void write64(uint32_t address,uint64_t value){W(address)=(uint32_t)value;W(address+4)=(uint32_t)(value>>32);}
void syscon_target_power_report(uint32_t printer){
    void (*out)(const char *,...)=(void (*)(const char *,...))(uintptr_t)printer;
    int32_t vph=(int32_t)syscon_target_power_measure(12);
    uint32_t header=syscon_target_power_measure(13),battery=syscon_target_power_measure(14);
    int32_t usb=(int32_t)syscon_target_power_measure(16),v18=(int32_t)syscon_target_power_measure(15);
    uint32_t vbatt=syscon_target_power_battery_route(),batt=syscon_target_retained_battery();
    uint32_t vbus=syscon_target_power_vbus_route(),hdr=syscon_target_power_header_route();
    out(S(0xcb61));out(S(0xcb76),table(0x2000006c,batt),battery);
    uint32_t id=syscon_target_power_battery_id();out(S(0xcb91),S(id==1?0xcb23:0xcb2c));
    uint32_t ntc=syscon_target_power_ntc();out(S(0xcba5),table(0x20000090,ntc));
    out(S(0xcbb9),S(usb>4499?0xcb34:0xcb3d),usb);
    uint32_t removed=syscon_target_pin_read(32);out(S(0xcbd4),S(removed?0xcb46:0xcb54));
    out(S(0xcbe8),table(0x20000060,hdr),header);
    uint32_t boost=syscon_target_power_boost();out(S(0xcc03),S(boost?0xb9f9:0xba07));
    out(S(0xcc17),table(0x20000084,vbus));out(S(0xcc2b),table(0x20000078,vbatt));
    out(S(0xcc3f),S(v18>1700?0xd1a9:0xd776),v18);
    out(S(0xcc5e),S(vph>3000?0xd1a9:0xd776),vph);out(S(0xcc7d));
}
int32_t syscon_target_power_policy_init(uint32_t cold){
    uint8_t config[7]={0,0,7,0,8,7,12};
    syscon_target_adc_init(12,(uint32_t)(uintptr_t)config);
    syscon_target_adc_init(13,(uint32_t)(uintptr_t)config);
    syscon_target_adc_init(14,(uint32_t)(uintptr_t)config);
    syscon_target_adc_init(15,(uint32_t)(uintptr_t)config);
    syscon_target_adc_init(16,(uint32_t)(uintptr_t)config);
    syscon_target_adc_init(23,(uint32_t)(uintptr_t)config);
    if(!cold)syscon_target_power_report((uint32_t)(uintptr_t)syscon_target_mfg_logger);
    else{
        uint8_t output[3]={1,0,1};
        static const uint8_t low[]={8,9,10,12,13,0,15,7,1};
        static const uint8_t high[]={2,3,11};
        for(unsigned i=0;i<sizeof(low);++i)syscon_target_ioexpander_configure(low[i],(const syscon_io_config *)output);
        output[1]=1;
        for(unsigned i=0;i<sizeof(high);++i)syscon_target_ioexpander_configure(high[i],(const syscon_io_config *)output);
    }return 0;
}
void syscon_target_power_minimum_update(void){
    int32_t measured=(int32_t)syscon_target_power_measure(12);
    if(measured<(int32_t)W(0x2000005c))W(0x2000005c)=(uint32_t)measured;
}
void syscon_target_power_minimum_reset(void){W(0x2000005c)=INT32_MAX;}
uint32_t syscon_target_power_minimum(void){uint32_t value=W(0x2000005c);return value==INT32_MAX?UINT32_MAX:value;}
void syscon_target_shutdown_set(uint32_t reason){
    syscon_target_logger(3,S(0xc68e),S(0xcc92),table(0x20000098,reason));
    B(0x2000036f)=(uint8_t)reason;B(0x20000380)=0;
    uint64_t now=reason?syscon_target_now():0;write64(0x20000388,now);
}
uint32_t syscon_target_shutdown_reason(void){return B(0x2000036f);}
uint64_t syscon_target_shutdown_elapsed(void){
    if(!read64(0x20000388))return 0;
    uint64_t now=syscon_target_now(),start=read64(0x20000388);
    return now>start?now-start:0;
}
uint32_t syscon_target_shutdown_stale(void){return B(0x20000380);}
uint32_t syscon_target_shutdown_active(void){return B(0x20000380)?0:B(0x2000036f);}
void syscon_target_shutdown_poll(void){
    uint32_t reason=B(0x2000036f);uint64_t start=read64(0x20000388),now=syscon_target_now();
    if(!B(0x20000380) && reason && start && now-start>299999){
        reason=B(0x2000036f);
        syscon_target_logger(2,S(0xc68e),S(0xccaa),table(0x20000098,reason),5);
        B(0x20000380)=1;
    }
}
