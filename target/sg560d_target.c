/* Source-backed original ARM32 SG560D entries, including diagnostics. */
#include "sg560d_target.h"
#include "sg560d_literals.h"
#include "runtime_memory.h"
#include "scheduling_target.h"
#include "power_manager_target.h"
#include "power_policy_target.h"
#include "power_state.h"
#include "mspm0_core_target.h"
#include "uart_hal_target.h"
#include "uart_ring_target.h"
#include "hal_helpers.h"
#include "ioexpander_target.h"
#include "rgb_target.h"
#include "power_key_target.h"
#include "adc_target.h"
#include "diagnostics_target.h"
#include "application_target.h"
#include "protocol_target.h"
#include "logger_target.h"
#define B(o) (*(volatile uint8_t *)(uintptr_t)(0x20000000u+(o)))
#define W(o) (*(volatile uint32_t *)(uintptr_t)(0x20000000u+(o)))
#define U32(a) (*(const volatile uint32_t *)(uintptr_t)(uint32_t)(a))
#define PTR(a) ((const char *)(uintptr_t)(uint32_t)(a))
#define D(a) D_##a
#define LOG(level,loc,...) syscon_target_logger(level,PTR(D_60e8),PTR(D(loc)),##__VA_ARGS__)
#define ADDRESS(p) ((uint32_t)(uintptr_t)(p))
static uint64_t read64(uint32_t offset){uint32_t lo=W(offset),hi=W(offset+4);return (uint64_t)lo|((uint64_t)hi<<32);}
static void write64(uint32_t offset,uint64_t value){W(offset)=(uint32_t)value;W(offset+4)=(uint32_t)(value>>32);}
static void check(uint32_t line,uint32_t condition){
    const char *file=PTR(D_5ecc),*base=file;
    if(syscon_rt_strrchr(file,'/'))base=(const char *)syscon_rt_strrchr(file,'/')+1;
    syscon_target_assert(ADDRESS(base),line,condition);
}
static int32_t measure(uint32_t pin){return (int32_t)syscon_target_power_measure(pin);}
void syscon_target_modem_uart_stop(void){
    if(B(0xed)){
        if(syscon_target_uart_deinit(1))check(0x105,D_5ed0);
        syscon_rt_memset((void *)0x200003d0,0,128);B(0xed)=0;
    }
    uint8_t config[12]={0};config[5]=2;
    uint32_t descriptor=syscon_hal_uart_lookup(1);
    if(!descriptor)check(0x116,D_5ed8);
    syscon_target_gpio_config(*(const uint8_t *)(uintptr_t)descriptor,ADDRESS(config));
    syscon_target_gpio_config(*(const uint8_t *)(uintptr_t)(descriptor+3),ADDRESS(config));
}
void syscon_target_modem_uart_start(void){
    if(B(0xed))return;
    const uint8_t config[9]={0,0,9,0,0,0xc2,1,0,0};
    if(syscon_target_uart_init(1,ADDRESS(config)))check(0xf8,D_61b0);
    syscon_rt_memset((void *)0x200003d0,0,128);B(0xed)=1;
}
uint32_t syscon_target_modem_power_check(void){
    int32_t battery=(int32_t)syscon_target_power_battery_detect();
    int32_t route=(int32_t)syscon_target_power_battery_route();
    LOG(3,60f0,syscon_power_name(syscon_power_names.battery_route,route));
    if(measure(15)>1699){LOG(1,60f8,1699);check(0x152,D_6100);}
    if(!syscon_target_hwrevision_new()){if(route)check(0x159,D_6134);}
    else if(route)LOG(1,6104);
    uint32_t direction=syscon_target_power_header_route();
    int32_t header=measure(13),battery_mv=measure(14);
    uint32_t input=header>4500&&direction<2;
    if(input)LOG(3,610c);else LOG(3,6138);
    int32_t usb=measure(16);
    if(usb<=4499)LOG(2,6114,usb);
    int32_t status=(int32_t)syscon_target_power_header_route_set(input?1:2);
    if(status<0){if(input)LOG(1,6118,status);else LOG(1,613c,status);}
    if(battery==1){
        if(battery_mv<2000){
            if(syscon_target_hwrevision_new()){
                LOG(1,6140);
                status=(int32_t)syscon_target_power_battery_route_set(2);if(status<0)LOG(1,6144,status);
                B(0x4f8)=1;
            }
        }else{status=(int32_t)syscon_target_power_battery_route_set(1);if(status<0)LOG(1,611c,status);}
    }else{status=(int32_t)syscon_target_power_battery_route_set(2);if(status<0)LOG(1,6144,status);}
    syscon_target_power_vbus_route_set(usb<=4499&&input&&battery==1?2:1);
    syscon_target_power_report(ADDRESS(syscon_target_mfg_logger));
    B(0x4f2)=1;write64(0x518,syscon_target_now()+3000);
    LOG(3,6130);return 1;
}
uint32_t syscon_target_modem_fct_complete(void){LOG(3,61c8);return 1;}
uint32_t syscon_target_modem_volume_release(void){LOG(3,61e8);syscon_target_pin_write(29,1);return 1;}
uint32_t syscon_target_modem_usbboot_release(void){LOG(3,6208);syscon_target_gpio_write(11,0);return 1;}
uint32_t syscon_target_modem_powerkey_release_task(void){LOG(3,6228);syscon_target_gpio_write(8,0);return 1;}
uint32_t syscon_target_modem_action_6230(void){return syscon_target_modem_powerkey_release_task();}
uint32_t syscon_target_modem_action_6238(void){return syscon_target_modem_powerkey_release_task();}
uint32_t syscon_target_modem_action_6240(void){return syscon_target_modem_powerkey_release_task();}
void syscon_target_modem_pins_off(void){
    const uint8_t gpio[12]={0};const syscon_io_config expander={0,0,1};
    syscon_target_gpio_config(8,ADDRESS(gpio));syscon_target_gpio_config(11,ADDRESS(gpio));
    syscon_target_ioexpander_configure(14,&expander);syscon_target_ioexpander_configure(4,&expander);
}
void syscon_target_modem_pins_on(void){
    uint8_t gpio[12]={0,0,0,0,1,0,0,0,2,0,0,0};const syscon_io_config expander={1,1,1};
    syscon_target_gpio_config(8,ADDRESS(gpio));syscon_target_gpio_config(11,ADDRESS(gpio));
    syscon_target_ioexpander_configure(14,&expander);syscon_target_ioexpander_configure(4,&expander);
    gpio[4]=0;gpio[5]=2;
    syscon_target_gpio_config(18,ADDRESS(gpio));syscon_target_gpio_config(19,ADDRESS(gpio));syscon_target_gpio_config(20,ADDRESS(gpio));
    syscon_target_modem_uart_stop();
}
uint32_t syscon_target_modem_retry_delay(uint32_t reason,uint32_t attempts){
    int32_t temperature=(int32_t)syscon_target_adc_temperature();
    uint32_t initial=reason<7?U32(D_6364+4*reason):900000,delay=initial;
    if(temperature>=500){
        if(initial<120000)delay=120000;
        if(initial<=119999)LOG(3,6374,temperature/10,temperature%10,syscon_power_name(syscon_power_names.shutdown,reason));
    }
    for(uint32_t i=0;i!=attempts;i++){if(delay>449999)return 900000;delay*=2;}
    return delay;
}
void syscon_target_modem_retry_schedule(uint32_t reason){
    uint32_t continuing=B(0x508)!=0&&B(0x528)==reason;B(0x528)=(uint8_t)reason;
    if(reason==0||reason-3<4){
        if(!continuing)W(0x4f4)=0;
        B(0x508)=1;
        uint32_t delay=syscon_target_modem_retry_delay(reason,W(0x4f4));write64(0x500,syscon_target_now()+delay);
        LOG(3,6420,syscon_power_name(syscon_power_names.shutdown,reason),continuing?D_6418:D_641c,delay/1000,W(0x4f4));
    }
}
#define ACTION(fn) {0,{0,0,0},(uint32_t)(uintptr_t)(fn)}
#define DELAY(ms) {1,{0,0,0},(ms)}
static const syscon_action boot_actions[]={
    ACTION(syscon_target_modem_prepare_normal),DELAY(2000),ACTION(syscon_target_modem_action_6230),
    ACTION(syscon_target_modem_prepare_edl),DELAY(2000),ACTION(syscon_target_modem_action_6240),ACTION(syscon_target_modem_usbboot_release),
    ACTION(syscon_target_modem_prepare_special),DELAY(2000),ACTION(syscon_target_modem_action_6238),DELAY(100),ACTION(syscon_target_modem_volume_release),DELAY(5000),
    ACTION(syscon_target_modem_action_74c8),DELAY(200),ACTION(syscon_target_modem_action_74a8),DELAY(200),ACTION(syscon_target_modem_action_7488),ACTION(syscon_target_modem_fct_complete)
};
uint32_t syscon_target_modem_poweron(void){
    if(B(0x4f1)){LOG(1,6488);return UINT32_MAX;}
    syscon_target_shutdown_set(0);B(0x508)=0;B(0x528)=0;
    syscon_target_modem_pins_on();syscon_target_wakeup_enable(0);
    syscon_action actions[3];syscon_rt_memcpy(actions,boot_actions,sizeof(actions));
    if(syscon_target_tasks_submit(actions,3)<0)LOG(3,649c);
    return 0;
}
uint32_t syscon_target_modem_edl(void){
    if(B(0x4f1)){LOG(1,6508);return UINT32_MAX;}
    syscon_target_shutdown_set(0);B(0x508)=0;B(0x528)=0;
    syscon_target_modem_pins_on();syscon_target_wakeup_enable(0);
    syscon_action actions[4];syscon_rt_memcpy(actions,boot_actions+3,sizeof(actions));
    if(syscon_target_tasks_submit(actions,4)<0)LOG(3,651c);
    return 0;
}
uint32_t syscon_target_modem_special_boot(uint32_t fct){
    if(B(0x4f1)){LOG(1,65a8);return UINT32_MAX;}
    syscon_target_shutdown_set(0);B(0x508)=0;B(0x528)=0;
    syscon_target_modem_pins_on();syscon_target_wakeup_enable(0);
    W(0x3c8)=fct?D_65b8:D_65bc;B(0x3c4)=fct?5:3;
    syscon_action actions[12];syscon_rt_memcpy(actions,boot_actions+7,sizeof(actions));
    if(syscon_target_tasks_submit(actions,fct?12:5)<0)LOG(3,65cc,W(0x3c8));
    return 0;
}
uint32_t syscon_target_modem_fct(void){return syscon_target_modem_special_boot(1);}
uint32_t syscon_target_modem_fct_callback(void){syscon_target_modem_special_boot(1);return 1;}
uint32_t syscon_target_modem_fastboot(void){return syscon_target_modem_special_boot(0);}
void syscon_target_modem_wake_schedule(uint32_t seconds){
    if(!seconds){if(read64(0x458))LOG(3,6644);write64(0x458,0);}
    else{write64(0x458,syscon_target_now()+(uint64_t)seconds*1000);LOG(3,664c,seconds);}
}
int32_t syscon_target_modem_wake_remaining(void){
    uint64_t now=syscon_target_now(),deadline=read64(0x458);
    if(!deadline)return -1;
    return now>=deadline?0:(int32_t)((deadline-now)/1000);
}
uint32_t syscon_target_modem_off(void){return B(0x4f1)==0;}
uint32_t syscon_target_modem_mode_name(uint32_t mode){
    const uint32_t names[]={0xd5ba,0xd73c,0xd328,0xdba1,0xd324};
    uint32_t index=(uint8_t)(mode-1);return index<5?names[index]:0xcceb;
}
uint32_t syscon_target_modem_set_mode(uint32_t mode){
    LOG(3,6714,syscon_target_modem_mode_name(mode));B(0x450)=(uint8_t)mode;
    syscon_target_retained_set_modem(mode);uint32_t key=0;
    switch(mode){
    case 1:syscon_target_rgb_preset(0,0);key=1;break;
    case 2:syscon_target_rgb_preset(4,0);break;
    case 3:syscon_target_rgb_preset(1,0);key=1;break;
    case 4:syscon_target_rgb_preset(2,0);key=1;break;
    case 5:syscon_target_rgb_preset(3,0);break;
    }
    syscon_target_powerkey_mode(key);return 0;
}
uint32_t syscon_target_modem_poweroff(uint32_t force){
    if(syscon_target_tasks_active()){LOG(3,67fc);return 0;}
    int32_t voltage=measure(15);
    if(voltage>1699||force){
        LOG(3,6808);
        int32_t status=(int32_t)syscon_target_power_vbus_route_set(0);if(status<0)LOG(1,680c,status);
        status=(int32_t)syscon_target_power_battery_route_set(0);if(status<0)LOG(1,6810,status);
        if(syscon_target_modem_always_on()){status=(int32_t)syscon_target_power_header_default();if(status<0)LOG(1,6814,status);}
        else{
            status=(int32_t)syscon_target_power_header_route_set(0);if(status<0)LOG(1,6830,status);
            status=(int32_t)syscon_target_power_boost_set(0);if(status<0)LOG(1,6834,status);
        }
        syscon_target_modem_set_mode(1);B(0x4f2)=3;write64(0x518,syscon_target_now()+3000);
    }
    syscon_target_modem_uart_stop();syscon_target_modem_pins_off();syscon_target_wakeup_enable(1);
    B(0x3cf)=0;B(0x4f8)=0;write64(0x4e8,0);return 1;
}
uint32_t syscon_target_modem_prepare_special(void){
    LOG(3,6894,W(0x3c8));uint32_t ok=syscon_target_modem_power_check();
    if(!ok){LOG(1,6898);syscon_target_modem_pins_off();syscon_target_wakeup_enable(1);}
    else{syscon_target_modem_set_mode(B(0x3c4));syscon_target_pin_write(29,0);syscon_target_gpio_write(8,1);W(0x454)=(uint32_t)syscon_target_now();}
    return ok;
}
uint32_t syscon_target_modem_prepare_edl(void){
    LOG(3,68f4);syscon_target_gpio_write(11,1);uint32_t ok=syscon_target_modem_power_check();
    if(!ok){LOG(1,68f8);syscon_target_modem_pins_off();syscon_target_wakeup_enable(1);syscon_target_gpio_write(11,0);}
    else{syscon_target_modem_set_mode(4);syscon_target_gpio_write(8,1);}return ok;
}
uint32_t syscon_target_modem_prepare_normal(void){
    LOG(3,6940);uint32_t ok=syscon_target_modem_power_check();
    if(!ok){LOG(1,6944);syscon_target_modem_pins_off();syscon_target_wakeup_enable(1);}
    else{syscon_target_modem_set_mode(2);syscon_target_gpio_write(8,1);}return ok;
}
uint32_t syscon_target_modem_init(uint32_t mode){
    syscon_target_modem_pins_on();int32_t voltage=measure(15);
    if(voltage>1699){
        if(mode<2){LOG(3,6a0c,1699);mode=2;}
        B(0x4f2)=2;B(0x4f1)=2;write64(0x4e0,syscon_target_now());
    }else{
        if(mode>1)LOG(1,6a20,syscon_target_modem_mode_name(mode));
        mode=1;B(0x4f2)=0;B(0x4f1)=0;
    }
    syscon_target_modem_set_mode(mode);uint32_t on=B(0x4f1)==2;
    LOG(3,6a1c,on?D_6a14:D_6a18);
    if(on){syscon_target_modem_uart_start();syscon_target_wakeup_enable(0);}
    else{syscon_target_modem_pins_off();syscon_target_wakeup_enable(1);
        if(syscon_target_modem_always_on()){int32_t status=(int32_t)syscon_target_power_header_default();if(status<0)LOG(1,6a24,status);}}
    return on;
}
void syscon_target_modem_key_assert(void){LOG(3,6a40);syscon_target_gpio_write(8,1);}
void syscon_target_modem_key_release(void){LOG(3,6a60);syscon_target_gpio_write(8,0);}
uint32_t syscon_target_modem_key_pulse(uint32_t pin,uint32_t initial){
    syscon_target_pin_write((uint8_t)pin,initial);syscon_target_timer_delay(250);syscon_target_pin_write((uint8_t)pin,initial^1);return 0;
}
uint32_t syscon_target_modem_action_7488(void){LOG(3,74a0);syscon_target_modem_key_pulse(8,1);return 1;}
uint32_t syscon_target_modem_action_74a8(void){LOG(3,74c0);syscon_target_modem_key_pulse(39,0);return 1;}
uint32_t syscon_target_modem_action_74c8(void){LOG(3,74e0);syscon_target_modem_key_pulse(39,0);return 1;}
uint32_t syscon_target_modem_raw_send(uint32_t data,uint32_t length){return syscon_target_uart_write_buffer(1,data,length);}

void syscon_target_modem_poll(void){
    syscon_target_shutdown_poll();int32_t v18=measure(15);
    if(v18>1699)syscon_target_power_minimum_update();
    if(read64(0x4e8)&&syscon_target_now()>=read64(0x4e8)){
        write64(0x4e8,0);B(0x4f8)=0;LOG(3,6bf4);
        syscon_target_power_battery_route_set(1);syscon_target_power_minimum_reset();
    }
    if(v18>1699){
        if(!B(0x4f1)){
            if(B(0x4f2)==1){
                B(0x4f1)=2;B(0x4f2)=2;write64(0x518,0);
                syscon_target_modem_uart_start();
                uint32_t vph=(uint32_t)measure(12),route=syscon_target_power_battery_route();
                LOG(3,6c08,vph,syscon_power_name(syscon_power_names.battery_route,route));
                if(B(0x4f8))write64(0x4e8,syscon_target_now()+50);
                syscon_target_power_minimum_reset();write64(0x4e0,syscon_target_now());
                if(read64(0x458)){LOG(3,6c14);write64(0x458,0);}
                if(B(0x3cf)){
                    B(0x3cf)=0;
                    uint32_t reason=syscon_target_shutdown_reason(),stale=syscon_target_shutdown_stale();
                    if(reason==1)LOG(3,6c24,stale?D_6c1c:D_6c20);
                    else LOG(2,6c44,syscon_power_name(syscon_power_names.shutdown,reason),stale?D_6c1c:D_6c20);
                    syscon_target_shutdown_set(0);B(0x508)=0;B(0x528)=0;
                    if(B(0x450)==5){
                        uint32_t elapsed=(uint32_t)syscon_target_now()-W(0x454);
                        if(elapsed){
                            if(elapsed>14999){
                                LOG(1,6fb8,elapsed);syscon_target_modem_poweroff(1);
                                const syscon_action retry[]={DELAY(3000),ACTION(syscon_target_modem_fct_callback)};
                                if(syscon_target_tasks_submit(retry,2)<0)LOG(3,6fc0);
                            }else LOG(3,6f80,elapsed);
                            goto transition_done;
                        }
                        LOG(3,6c38,elapsed);
                    }
                    if(B(0x450)!=2){LOG(3,6c3c,B(0x450));syscon_target_modem_set_mode(2);}
                }else LOG(3,6fc4);
            }else if(!B(0x4f2)){
                LOG(1,6fd0);B(0x4f1)=2;B(0x4f2)=2;write64(0x518,0);
                syscon_target_modem_uart_start();syscon_target_wakeup_enable(0);syscon_target_modem_set_mode(2);
            }
        }
    }else if(B(0x4f1)==2){
        if(B(0x4f2)==3){
            B(0x4f2)=0;write64(0x518,0);B(0x4f1)=0;
            syscon_target_modem_uart_stop();write64(0x4e0,0);LOG(3,6fcc);
        }else if(B(0x4f2)==2){
            syscon_target_power_minimum_update();uint32_t floor=syscon_target_power_minimum();
            uint32_t battery=(uint32_t)measure(14);
            if(!syscon_target_shutdown_reason()&&floor<=2499)syscon_target_shutdown_set(6);
            uint32_t reason=syscon_target_shutdown_reason(),stale=syscon_target_shutdown_stale();
            LOG(2,6fe4,syscon_power_name(syscon_power_names.shutdown,reason),stale?D_6fdc:D_6fe0,floor,battery);
            syscon_target_power_minimum_reset();reason=syscon_target_shutdown_active();
            B(0x4f2)=1;B(0x3cf)=1;write64(0x4e0,0);B(0x4f1)=0;
            write64(0x518,syscon_target_now()+250);syscon_target_modem_retry_schedule(reason);
        }
    }
transition_done:
    if(read64(0x518)&&syscon_target_now()>read64(0x518)){
        if(!B(0x3cf)){
            if(!B(0x4f1)&&B(0x4f2)==1){
                LOG(1,7308);uint32_t mode=B(0x450);syscon_target_modem_poweroff(1);
                if(mode-3>2)syscon_target_modem_retry_schedule(syscon_target_shutdown_active());
            }else LOG(1,7310);
        }else if(!B(0x4f1)&&B(0x4f2)==1){
            B(0x3cf)=0;uint32_t reason=syscon_target_shutdown_active();
            if(reason==1){LOG(3,6f94);syscon_target_modem_poweron();}
            else{
                if((uint8_t)(reason-3)<4||!reason)LOG(3,6fec,syscon_power_name(syscon_power_names.shutdown,reason));
                else LOG(3,6fe8);
                syscon_target_modem_poweroff(1);
            }
        }else LOG(1,7310);
        B(0x4f2)=B(0x4f1);write64(0x518,0);
    }
    uint8_t samples[3];
    samples[0]=syscon_target_gpio_read(18)==1;samples[1]=syscon_target_gpio_read(19)==1;samples[2]=syscon_target_gpio_read(20)==1;
    for(unsigned i=0;i<3;i++)B(0x4f9+i)=(uint8_t)((B(0x4f9+i)<<1)|samples[i]);
    uint8_t rgb[3];syscon_rt_memset(rgb,0,3);syscon_rt_memcpy(rgb,(void *)0x200003cc,3);
    for(unsigned i=0;i<3;i++){if(!B(0x4f9+i))rgb[i]=0;else if((B(0x4f9+i)&7)==7)rgb[i]=1;}
    if(syscon_rt_memcmp((void *)0x200003cc,rgb,3)){
        LOG(3,6fa8,rgb[0]?D_6fa0:D_6fa4,rgb[1]?D_6fa0:D_6fa4,rgb[2]?D_6fa0:D_6fa4);
        W(0x530)=(uint32_t)syscon_target_now();
        if(!rgb[0]&&rgb[1]&&!rgb[2])W(0x52c)=(uint32_t)syscon_target_now();
        if(!rgb[0]&&!rgb[1]&&!rgb[2]&&syscon_target_now()-(uint64_t)W(0x52c)<150){LOG(3,7318,0);LOG(3,731c);}
        B(0x3cc)=rgb[0];B(0x3cd)=rgb[1];B(0x3ce)=rgb[2];
    }
    uint32_t green=0,cyan=0,yellow=0;
    if(rgb[1]){
        green=rgb[1];
        if(!rgb[0]){if(rgb[2]){green=0;cyan=rgb[2];}}
        else{green=0;yellow=rgb[2]^1;}
    }
    uint32_t stable=W(0x530)&&syscon_target_now()-(uint64_t)W(0x530)>=1001;
    uint32_t preset=syscon_target_rgb_state();
    if(stable){
        uint32_t desired=green?5:cyan?6:yellow?7:0;
        if(desired&&preset!=desired){LOG(3,7320,preset,desired);syscon_target_rgb_preset(desired,0);}
        else LOG(3,6fb4,preset);
        W(0x530)=0;
    }
    syscon_target_protocol_poll(0x200000e0);
    int32_t usb=measure(16);uint32_t present=usb>4499;
    if(!B(0x50a)){B(0x4f0)=(uint8_t)present;B(0x50a)=1;}
    uint8_t current=B(0x4f1),expected=B(0x4f2);uint32_t automatic=syscon_target_auto_boot();
    if(!current&&!expected){
        if(read64(0x458)&&syscon_target_now()>=read64(0x458)){
            int32_t temperature=(int32_t)syscon_target_adc_temperature(),header=measure(13);
            uint32_t reason=syscon_target_shutdown_reason();uint64_t age=syscon_target_shutdown_elapsed();
            uint32_t permitted=0;
            if(temperature<500){
                if(reason==3)permitted=(usb>4499||header>4499)&&age>=U32(D_7358+reason*4);
                else if((uint8_t)(reason-3)<4||!reason)permitted=age>=U32(D_7358+reason*4);
                else permitted=1;
            }
            if(permitted){LOG(3,735c);write64(0x458,0);syscon_target_modem_poweron();}
            else if(syscon_target_now()>=read64(0x510)){
                write64(0x510,syscon_target_now()+60000);
                const char *name=syscon_power_name(syscon_power_names.shutdown,reason);uint64_t elapsed=syscon_target_shutdown_elapsed();
                LOG(2,7350,name,(uint32_t)(elapsed/1000),temperature/10,temperature%10);
            }
        }
        if(automatic&&B(0x508)&&!syscon_target_power_shutdown_busy()){
            if(syscon_target_now()>=read64(0x500)){
                uint32_t blocked=0;
                if(B(0x528)==3){int32_t header=measure(13);blocked=usb<=4499&&header<=4499;}
                if(!blocked){
                    uint8_t reason=B(0x528);W(0x4f4)=W(0x4f4)+1;
                    uint32_t delay=syscon_target_modem_retry_delay(reason,W(0x4f4));write64(0x500,syscon_target_now()+delay);
                    LOG(3,7370,W(0x4f4),syscon_power_name(syscon_power_names.shutdown,reason),delay/1000);
                    syscon_target_modem_poweron();B(0x528)=reason;B(0x508)=1;B(0x509)=0;
                }
            }
        }
    }
    if(B(0x508)&&read64(0x4e0)&&B(0x4f1)==2&&syscon_target_now()-read64(0x4e0)>119999){
        LOG(3,7380,120,W(0x4f4));W(0x4f4)=0;B(0x508)=0;B(0x528)=0;
    }
    uint32_t reason=syscon_target_shutdown_active();
    uint32_t owns=B(0x508)&&B(0x528)?B(0x508):reason==2;
    if(!syscon_target_power_shutdown_busy()&&!current&&!expected&&automatic){
        if(!owns){
            if(!B(0x4f0)&&present){
                write64(0x520,syscon_target_now());B(0x509)=1;LOG(3,7454,D_7458);goto usb_done;
            }
            if(!B(0x509)){if(present)goto usb_done;}
            else if(present){
                if(syscon_target_now()-read64(0x520)>4999){LOG(3,7460);B(0x509)=0;syscon_target_modem_poweron();}
                goto usb_done;
            }else LOG(3,7464);
        }else if(!B(0x4f0)&&present){
            uint32_t selected=B(0x508)?B(0x528):reason;
            LOG(3,7448,syscon_power_name(syscon_power_names.shutdown,selected));
        }
    }
    B(0x509)=0;
usb_done:
    B(0x4f0)=(uint8_t)present;
}
