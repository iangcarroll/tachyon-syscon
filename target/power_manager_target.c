#include "power_manager_target.h"
#include "runtime_memory.h"
#include "scheduling_target.h"
#include "fault_control_target.h"
#include "adc_target.h"
#define U8(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))
extern uint32_t syscon_target_pin_read(uint32_t pin);
extern uint32_t syscon_target_pin_write(uint32_t pin,uint32_t value);
#define LOG(level,format,...) syscon_target_logger(level,(const char *)0xc68eu,(const char *)(uintptr_t)(format),##__VA_ARGS__)
static void power_assert(uint32_t line,uint32_t expression) {
    uint32_t file=0xc61fu;
    if(syscon_rt_strrchr((void *)(uintptr_t)file,'/'))file=(uint32_t)(uintptr_t)syscon_rt_strrchr((void *)(uintptr_t)file,'/')+1u;
    syscon_target_assert(file,line,expression);
}
uint32_t syscon_target_power_measure(uint32_t pin) {
    uint32_t sample=syscon_target_adc_millivolts((uint16_t)pin);
    if(!sample)sample=syscon_target_adc_millivolts((uint16_t)pin);
    uint32_t index;
    if(pin>=12u&&pin<=16u)index=pin-12u;
    else if(pin==23u)index=5;else return 0;
    return sample*U8(0xcd70u+index*2u);
}
static uint32_t selector(uint32_t first,uint32_t second,uint32_t line) {
    uint32_t a=syscon_target_pin_read(first),b=syscon_target_pin_read(second);
    if(a==0&&b==1)return 2;
    if(a<=1&&b==0)return a;
    power_assert(line,0xae64u);return 0;
}
uint32_t syscon_target_power_battery_route(void){return selector(33,34,0x131);}
uint32_t syscon_target_power_vbus_route(void){return selector(35,26,0x17c);}
uint32_t syscon_target_power_header_route(void){return selector(40,25,0x1a2);}
uint32_t syscon_target_power_battery_id(void){return syscon_target_pin_read(38)!=0;}
uint32_t syscon_target_power_ntc(void){return syscon_target_pin_read(36)!=0;}
uint32_t syscon_target_power_boost(void){return syscon_target_pin_read(37)!=0;}
uint32_t syscon_target_power_battery_id_set(uint32_t v){LOG(3,0xc67f,v?0xc671u:0xc669u);return syscon_target_pin_write(38,v!=0);}
uint32_t syscon_target_power_ntc_set(uint32_t v){uint32_t name=U32(0x20000090u+v*4u);LOG(3,0xc693,name);return syscon_target_pin_write(36,v!=0);}
uint32_t syscon_target_power_boost_set(uint32_t v){return syscon_target_pin_write(37,v);}
uint32_t syscon_target_power_battery_sense_set(uint32_t v){return syscon_target_pin_write(27,v!=0);}
uint64_t syscon_target_power_battery_route_set(uint32_t v) {
    uint32_t old=syscon_target_power_battery_route();
    if(old==v){uint32_t name=U32(0x20000078u+old*4u);LOG(3,0xc6a6,name);return (uint64_t)v<<32;}
    if(old){syscon_target_pin_write(33,0);syscon_target_pin_write(34,0);}
    if(v==1){syscon_target_power_ntc_set(0);syscon_target_power_battery_id_set(0);syscon_target_pin_write(33,1);}
    else if(v==2){syscon_target_power_ntc_set(1);syscon_target_power_battery_id_set(1);syscon_target_pin_write(34,1);}
    else syscon_target_power_ntc_set(1);
    uint32_t nextname=U32(0x20000078u+v*4u),oldname=U32(0x20000078u+old*4u);
    LOG(3,0xc6c1,oldname,nextname);return (uint64_t)nextname<<32;
}
uint64_t syscon_target_power_header_route_set(uint32_t v) {
    LOG(3,0xc6d6);syscon_target_power_boost_set(1);syscon_target_timer_delay(20);
    uint32_t voltage=syscon_target_power_measure(13);if((int32_t)voltage<=4499)LOG(1,0xc6e8,voltage);
    if(v==1){LOG(3,0xc711);syscon_target_pin_write(25,0);syscon_target_pin_write(40,1);}
    else if(v==2){LOG(3,0xc71e);syscon_target_pin_write(40,0);syscon_target_pin_write(25,1);}
    else{syscon_target_timer_delay(20);syscon_target_pin_write(25,0);syscon_target_pin_write(40,0);}
    if(syscon_target_power_header_route()!=v){uint32_t actual=syscon_target_power_header_route();LOG(1,0xc72c,actual,v);}
    if(syscon_target_power_header_route()!=v)power_assert(0x1e6,0xc752);
    return (uint64_t)v<<32;
}
uint32_t syscon_target_power_header_default(void) {
    if(syscon_target_power_header_route()==1){LOG(3,0xc774);return 0;}
    LOG(3,0xc7a5);return (uint32_t)syscon_target_power_header_route_set(2);
}
uint32_t syscon_target_power_usb_isolate(uint32_t v) {
    LOG(3,0xc7d6,v?0xd079u:0xd085u);
    uint32_t a=syscon_target_pin_write(32,v!=0),b=syscon_target_pin_write(28,v==0);return a+b;
}
uint64_t syscon_target_power_vbus_route_set(uint32_t v) {
    uint32_t old=syscon_target_power_vbus_route();
    if(old==v){uint32_t name=U32(0x20000084u+old*4u);LOG(1,0xc7ed,name);return (uint64_t)v<<32;}
    uint32_t nextname=U32(0x20000084u+v*4u),oldname=U32(0x20000084u+old*4u);LOG(3,0xc807,oldname,nextname);
    if(v<=1){syscon_target_pin_write(35,v);syscon_target_pin_write(26,0);syscon_target_power_usb_isolate(0);}
    else if(v==2){syscon_target_pin_write(26,1);syscon_target_pin_write(35,0);syscon_target_power_usb_isolate(1);}
    if(syscon_target_power_vbus_route()!=v)power_assert(0x168,0xc81a);
    return (uint64_t)nextname<<32;
}
uint32_t syscon_target_power_usb_release_callback(void) {
    uint32_t result=syscon_target_power_usb_isolate(0);if((int32_t)result<0)LOG(1,0xc82f,result);
    uint64_t now=syscon_target_now();U32(0x20000378u)=(uint32_t)now;U32(0x2000037cu)=(uint32_t)(now>>32);
    U8(0x20000370u)=0;LOG(3,0xc87d,2000u);return 1;
}
uint32_t syscon_target_power_usb_assert_callback(void) {
    LOG(3,0xc8a4,250u);uint32_t result=syscon_target_power_usb_isolate(1);if((int32_t)result<0)LOG(1,0xc8d0,result);return 1;
}
uint32_t syscon_target_power_shutdown_busy(void) {
    uint32_t active=U8(0x20000370u);if(active)return active;
    uint32_t lo=U32(0x20000378u),hi=U32(0x2000037cu);if(!(lo|hi))return 0;
    uint64_t now=syscon_target_now();lo=U32(0x20000378u);hi=U32(0x2000037cu);
    return now-((uint64_t)hi<<32|lo)<2000u;
}
uint32_t syscon_target_power_shutdown_request(void) {
    if(syscon_target_power_shutdown_busy()){LOG(2,0xc91d);return UINT32_MAX;}
    uint32_t voltage=syscon_target_power_measure(16);if((int32_t)voltage<=4499){LOG(3,0xc93f,voltage);return UINT32_MAX;}
    if(!syscon_target_power_boost()){LOG(2,0xc971);return UINT32_MAX;}
    const uint32_t words[6]={0,(uint32_t)(uintptr_t)&syscon_target_power_usb_assert_callback,1,250,0,(uint32_t)(uintptr_t)&syscon_target_power_usb_release_callback};
    U8(0x20000370u)=1;U32(0x20000378u)=0;U32(0x2000037cu)=0;
    if(syscon_target_tasks_submit((const syscon_action *)words,3)<0){LOG(1,0xc9ad);U8(0x20000370u)=0;return UINT32_MAX;}
    return 0;
}
uint32_t syscon_target_power_battery_detect(void) {
    uint32_t voltage=syscon_target_power_measure(14),type;
    if((int32_t)voltage>2999){LOG(3,0xcb03,voltage);type=1;}
    else {
        uint32_t result=(uint32_t)syscon_target_power_battery_route_set(2);if((int32_t)result<0)LOG(1,0xc9cc,result);
        syscon_target_power_ntc_set(1);result=syscon_target_power_battery_sense_set(0);if((int32_t)result<0)LOG(1,0xca14,result);
        voltage=syscon_target_power_measure(23);LOG(3,0xca5f,voltage);
        result=(uint32_t)syscon_target_power_battery_route_set(0);if((int32_t)result<0)LOG(1,0xca6f,result);
        result=syscon_target_power_battery_sense_set(1);type=((voltage-400u)>800u)+1u;
        if((int32_t)result<0)LOG(1,0xcab7,result);
    }
    uint32_t name=U32(0x2000006cu+type*4u);LOG(3,0xcb17,name);
    syscon_target_retained_set_battery(type);syscon_target_power_ntc_set(0);return type;
}
