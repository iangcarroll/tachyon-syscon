/* Firmware 1.0.52 application entry and fixed-layout glue. No host dispatch. */
#include "application_target.h"
#include "diagnostics_target.h"
#include "scheduling_target.h"
#include "mspm0_core_target.h"
#include "fault_control_target.h"
#include "uart_hal_target.h"
#include "runtime_support.h"
#include "sg560d_target.h"
#include "rgb_target.h"
#include "power_key_target.h"
#include "power_manager_target.h"
#include "power_policy_target.h"
#include "ioexpander_target.h"
#include "protocol_target.h"
#include "uart_ring_target.h"
#include "config_helpers.h"
#include <stdint.h>
#define B(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define W(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))
#define S(a) ((const char *)(uintptr_t)(a))
#define Q 0x200002d8u
#define P 0x200002edu

void syscon_target_timestamp_constructor(void){W(0x200002ccu)=(uint32_t)syscon_target_now();}
void syscon_target_queue_destructor(void *queue){(void)queue;}
void syscon_target_queue_constructor(void){
    W(Q)=0x200002d1u;W(Q+4)=4;W(Q+12)=0;W(Q+8)=0;B(Q+16)=0;
    syscon_rt_arm_atexit((void *)(uintptr_t)Q,syscon_target_queue_destructor,(void *)0x2000060cu);
}
uint32_t syscon_target_queue_count(uint32_t q){
    if(B(q+16))return W(q+4);
    uint32_t write=W(q+8),read=W(q+12);
    if(write>=read){write=W(q+8);read=W(q+12);return write-read;}
    read=W(q+12);write=W(q+8);uint32_t size=W(q+4);return write+size-read;
}
static uint32_t modulo(uint32_t value,uint32_t size){return size?value%size:value;}
void syscon_target_queue_event(uint32_t event){
    if(B(Q+16)){syscon_target_logger(1,S(0xb4d6),S(0xb4ac),UINT32_MAX);return;}
    uint32_t index=W(Q+8),buffer=W(Q),size=W(Q+4);
    B(buffer+index)=(uint8_t)event;
    index=W(Q+8)+1;W(Q+8)=modulo(index,size);
    index=W(Q+8);uint32_t read=W(Q+12);
    if(index==read)B(Q+16)=1;
}
void syscon_target_request_off(void){
    if(!syscon_target_power_shutdown_request())B(0x200002ecu)=1;
    else syscon_target_modem_poweroff(0);
}
void syscon_target_diagnostic_write(uint32_t data,uint32_t length){
    syscon_target_fault_stage_set(17);syscon_target_uart_write_buffer(0,data,length);
}
void syscon_target_parser_poll(void){syscon_target_protocol_poll(0x20000048u);}
void syscon_target_log_enable(uint32_t enabled){B(0x2000080cu)=(uint8_t)enabled;}
void syscon_target_application_gpio_init(void){
    uint8_t cfg[12]={0};cfg[5]=2;
    syscon_target_gpio_config(10,(uint32_t)(uintptr_t)cfg);
    syscon_target_gpio_config(9,(uint32_t)(uintptr_t)cfg);
    syscon_target_gpio_config(24,(uint32_t)(uintptr_t)cfg);
}
void syscon_target_wakeup_irq(uint32_t pin,uint32_t context){
    (void)context;
    if(syscon_target_modem_off()){
        syscon_target_logger(3,S(0xdd18),S(0xdd05));
        syscon_target_timer_wait_countflags(10);
        if(!syscon_target_gpio_read(pin)){
            syscon_target_logger(3,S(0xdd18),S(0xdd1d));B(0x20000680u)=1;
        }else syscon_target_logger(3,S(0xdd18),S(0xdd32));
    }else syscon_target_logger(3,S(0xdd18),S(0xdd46));
}
void syscon_target_wakeup_init(void){
    uint8_t cfg[12]={0};syscon_target_gpio_config(17,(uint32_t)(uintptr_t)cfg);
}
void syscon_target_wakeup_enable(uint32_t enabled){
    if(enabled && syscon_target_wakeup_enabled()){
        syscon_target_logger(3,S(0xdd18),S(0xdd58));
        syscon_target_gpio_attach(17,2,(uint32_t)(uintptr_t)syscon_target_wakeup_irq,0);
    }else{
        syscon_target_logger(3,S(0xdd18),S(0xdd69));syscon_target_gpio_detach(17);
    }
}
void syscon_target_wakeup_poll(void){
    if(B(0x20000680u)){syscon_target_modem_poweron();B(0x20000680u)=0;}
}

_Noreturn void syscon_target_main(void){
    syscon_target_watchdog_init();uint32_t previous_stage=syscon_target_fault_stage_get();
    syscon_target_fault_stage_set(1);syscon_target_enable_mftick();
    uint8_t uart[9]={0,0,9,0,0,0xc2,1,0,0};
    syscon_target_uart_init(0,(uint32_t)(uintptr_t)uart);
    syscon_target_log_enable(1);syscon_target_retained_load();syscon_target_timer_init();
    syscon_target_tasks_init();syscon_target_watchdog_feed();syscon_target_config_init();
    syscon_target_wakeup_init();syscon_target_rgb_init(0);
    uint32_t reset=syscon_target_reset_cause();
    if(reset!=1 && reset!=6)syscon_target_retained_increment_boots();
    syscon_target_powerkey_init(0);
    syscon_target_powerkey_callback((uint32_t)(uintptr_t)syscon_target_queue_event,0);
    syscon_target_watchdog_feed();
    int32_t result=syscon_target_ioexpander_init(reset<2);
    if(result<0)syscon_target_logger(1,S(0xb4d6),S(0xb4db),result);
    syscon_target_logger(3,S(0xb4d6),S(0xb507));
    uint32_t reset_name=syscon_target_reset_cause_name(reset);
    uint32_t raw=syscon_target_cached_reason();
    uint32_t stage_name=syscon_target_fault_stage_name(previous_stage);
    syscon_target_logger(3,S(0xb4d6),S(0xb50e),S(0xf7f8),reset_name,raw,stage_name);
    syscon_target_logger(3,S(0xb4d6),S(0xb545),S(0xb539),S(0xb554));
    uint32_t mode=syscon_target_retained_modem();
    uint32_t mode_name=syscon_target_modem_mode_name(mode);
    uint32_t battery=syscon_target_retained_battery();
    uint32_t battery_name=W(0x2000006cu+(battery<<2));
    uint32_t boots=syscon_target_retained_boots();
    syscon_target_logger(3,S(0xb4d6),S(0xb55d),mode_name,battery_name,boots);
    syscon_target_logger(3,S(0xb4d6),S(0xb507));
    result=syscon_target_power_policy_init(reset<2);
    if(result<0)syscon_target_logger(1,S(0xb4d6),S(0xb589),result);
    mode=syscon_target_retained_modem();result=syscon_target_modem_init(mode);
    if(result<0)syscon_target_logger(1,S(0xb4d6),S(0xb5b7),result);
    syscon_target_application_gpio_init();syscon_target_watchdog_feed();
    if(reset==1){
        uint32_t automatic=syscon_target_auto_boot();
        if(syscon_target_factory_test())syscon_target_rgb_preset(7,0);
        else if(automatic)syscon_target_modem_poweron();
    }
    for(;;){
        syscon_target_fault_stage_set(2);syscon_target_diagnostics_poll();
        syscon_target_fault_stage_set(3);
        if(!B(0x200002ecu) && syscon_target_queue_count(Q)){
            uint32_t event;
            if(!syscon_target_queue_count(Q)){
                syscon_target_logger(1,S(0xb4d6),S(0xb5d4),UINT32_MAX);event=255;
            }else{
                uint32_t index=W(Q+12),next=W(Q+12)+1,buffer=W(Q),size=W(Q+4);
                event=B(buffer+index);W(Q+12)=modulo(next,size);B(Q+16)=0;
            }
            if(!syscon_target_factory_test()){
                if(event<6){
                    uint32_t old=B(P);
                    static const uint32_t formats[6]={0xb5fe,0xb62e,0xb647,0xb65b,0xb674,0xb687};
                    syscon_target_logger(3,S(0xb4d6),S(formats[event]),old);
                    switch(event){
                    case 0:{
                        uint32_t off=syscon_target_modem_off();B(P)=(uint8_t)off;
                        uint32_t alt=syscon_target_alt_powerkey();
                        syscon_target_logger(3,S(0xb4d6),S(0xb612),S(off?0xd1a9:0xd776),S(alt?0xb9f9:0xba07));
                        if(B(P) && syscon_target_alt_powerkey())syscon_target_rgb_key_feedback();
                        break;
                    }
                    case 1:if(B(P))syscon_target_modem_poweron();break;
                    case 2:
                        if(syscon_target_alt_powerkey())syscon_target_rgb_key_feedback();
                        else if(B(P))syscon_target_modem_edl();else syscon_target_request_off();
                        break;
                    case 3:{
                        uint32_t off=B(P);
                        if(syscon_target_alt_powerkey()){
                            if(off)syscon_target_modem_edl();else syscon_target_request_off();
                        }break;
                    }
                    case 4:if(syscon_target_alt_powerkey() && B(P))syscon_target_rgb_key_feedback();break;
                    case 5:if(B(P) && syscon_target_alt_powerkey())syscon_target_modem_fastboot();break;
                    }
                }else syscon_target_logger(1,S(0xb4d6),S(0xb69f),event);
            }
        }
        syscon_target_fault_stage_set(4);syscon_target_parser_poll();
        syscon_target_fault_stage_set(5);syscon_target_modem_poll();syscon_target_watchdog_feed();
        syscon_target_fault_stage_set(6);syscon_target_tasks_poll();syscon_target_fault_stage_set(7);
        if(B(0x200002ecu) && !syscon_target_tasks_active()){
            B(0x200002ecu)=0;syscon_target_modem_poweroff(1);
        }
        syscon_target_fault_stage_set(8);syscon_target_wakeup_poll();
    }
}
