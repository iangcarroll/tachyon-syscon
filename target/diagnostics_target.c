/* Original target configuration accessors and diagnostic loop. */
#include "diagnostics_target.h"
#include "runtime_scan.h"
#include "scheduling_target.h"
#include "power_manager_target.h"
#include "mspm0_core_target.h"
#include "adc_target.h"
#include "sg560d_target.h"
#include "power_policy_target.h"
#include "logger_target.h"
#include <stdint.h>
#define U8(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))
#define TEXT(a) ((const char *)(uintptr_t)(uint32_t)(a))

uint32_t syscon_target_auto_boot(void){return U8(0x20000030u);}
uint32_t syscon_target_wakeup_enabled(void){return U8(0x20000031u);}
uint32_t syscon_target_log_color(void){return U8(0x20000032u);}
uint32_t syscon_target_alt_powerkey(void){return U8(0x20000033u);}
uint32_t syscon_target_factory_test(void){return U8(0x20000034u);}
uint32_t syscon_target_modem_always_on(void){return U8(0x20000035u);}
static uint32_t packed_read(uint32_t base){
    /* Preserve the original nonmonotonic byte read order at unaligned fields. */
    uint32_t second=U8(base+1u),first=U8(base),third=U8(base+2u),fourth=U8(base+3u);
    return first|(second<<8)|(third<<16)|(fourth<<24);
}
uint32_t syscon_target_powerkey_long_seconds(void){return packed_read(0x20000036u);}
uint32_t syscon_target_powerkey_extra_seconds(void){return packed_read(0x2000003au);}
uint32_t syscon_target_hwrevision_new(void){
    uint32_t major,minor,patch=0;
    int fields=syscon_rt_sscanf(TEXT(0x2000003e),TEXT(0xb1a8),&major,&minor,&patch);
    return fields==3 && major==1 && minor>1;
}
void syscon_target_diagnostics_enable(uint32_t enabled){U8(0x20000046u)=(uint8_t)enabled;}
static uint64_t read64(uint32_t address){
    uint32_t low=U32(address),high=U32(address+4u);
    return ((uint64_t)high<<32)|low;
}
static void write64(uint32_t address,uint64_t value){
    U32(address)=(uint32_t)value;U32(address+4u)=(uint32_t)(value>>32);
}
void syscon_target_diagnostics_poll(void){
    write64(0x200002c0u,read64(0x200002c0u)+1u);
    uint64_t now=syscon_target_now();
    uint32_t previous_check=U32(0x200002c8u);
    if(now-(uint64_t)previous_check<=5000)return;
    uint32_t current=(uint32_t)syscon_target_now();
    uint32_t previous=U32(0x200002ccu);U32(0x200002ccu)=current;
    uint64_t loops=read64(0x200002c0u);write64(0x200002c0u,0);
    U32(0x200002c8u)=current;
    if(!U8(0x20000046u))return;
    uint32_t uptime=(uint32_t)(syscon_target_now()/1000u);
    uint32_t vph=syscon_target_power_measure(12);
    uint32_t v5=syscon_target_power_measure(13);
    uint32_t vbat=syscon_target_power_measure(14);
    uint32_t vusb=syscon_target_power_measure(16);
    uint32_t v1v8=syscon_target_power_measure(15);
    uint32_t wake=syscon_target_gpio_read(17);
    int32_t temperature=(int32_t)syscon_target_adc_temperature();
    uint8_t text[12];
    if(temperature==INT32_MIN)syscon_target_snprintf(text,12,TEXT(0xcb73));
    else{
        int32_t whole=temperature/10;
        uint32_t magnitude=temperature<0?0u-(uint32_t)temperature:(uint32_t)temperature;
        uint32_t fraction=magnitude%10;
        if(temperature<0 && whole==0)syscon_target_snprintf(text,12,TEXT(0xb24c),fraction);
        else syscon_target_snprintf(text,12,TEXT(0xd9ea),whole,fraction);
    }
    uint32_t off=syscon_target_modem_off();
    uint32_t minimum=syscon_target_power_minimum();
    syscon_target_logger(3,TEXT(0xb290),TEXT(0xb253),vph,v5,vbat,v1v8,vusb,minimum);
    uint32_t seconds=(current-previous)/1000u;
    /* The original public __aeabi_uldivmod explicitly returns all ones on
     * nonzero/zero and zero on zero/zero. Do not express C division-by-zero. */
    uint64_t rate=seconds?loops/seconds:(loops?UINT64_MAX:0);
    syscon_target_logger(3,TEXT(0xb290),TEXT(0xb295),uptime,(uint32_t)(uint8_t)(off^1u),
        (uint32_t)rate,TEXT(wake?0xcd10:0xcd1d),text);
}
