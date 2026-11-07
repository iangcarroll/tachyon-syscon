/* Original power-key ABI and split RAM layout. All callbacks/dependencies are
 * ordinary target function calls; no host dispatch or private state copy. */
#include "power_key_target.h"
#include "scheduling_target.h"
#include "mspm0_core_target.h"
#include "diagnostics_target.h"
#include "runtime_memory.h"
#define B(a) (*(volatile uint8_t *)(uintptr_t)(a))
#define H(a) (*(volatile uint16_t *)(uintptr_t)(a))
#define W(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define MODE B(0x200000d8)
#define EVENT B(0x200000d9)
#define PRESSED W(0x20000390)
#define CALLBACK W(0x20000394)
#define RELEASED W(0x20000398)
#define PENDING B(0x2000039c)
#define FORCED B(0x2000039d)
#define CONTEXT W(0x200003a0)
#define PIN H(0x200003a4)
#define ADDRESS(fn) ((uint32_t)(uintptr_t)(fn))
static void attach(void){(void)syscon_target_gpio_attach(0,0,ADDRESS(syscon_target_powerkey_edge),0);}
int syscon_target_powerkey_edge(uint32_t pin){
    (void)syscon_target_gpio_read(pin);
    syscon_target_timer_unregister(ADDRESS(syscon_target_powerkey_poll));
    PIN=(uint16_t)pin;
    (void)syscon_target_gpio_detach(0);
    return syscon_target_timer_register(10,1,ADDRESS(syscon_target_powerkey_debounce),0);
}
void syscon_target_powerkey_poll(uint32_t ignored){
    (void)ignored;uint8_t old=EVENT;
    if(!syscon_target_gpio_read(0)){
        PRESSED=PRESSED+10;RELEASED=0;
        if(!MODE && !FORCED && PRESSED>5999){syscon_target_modem_key_release();FORCED=1;}
    }else{PENDING=1;RELEASED=RELEASED+10;PRESSED=0;}
    for(unsigned i=0;i<3;++i){
        uintptr_t range=0x200000b4+12*i;
        uint32_t pressed=PRESSED,start=W(range);
        if(start>pressed)continue;
        pressed=PRESSED;uint32_t end=W(range+4);
        if(end>pressed){EVENT=B(range+8);break;}
    }
    uint8_t finished=PENDING;
    if(finished){if(RELEASED<=200)finished=0;else EVENT=EVENT+1;}
    if(EVENT!=old){
        uint32_t callback=CALLBACK;
        if(callback){uint8_t event=EVENT;uint32_t context=CONTEXT;
            ((void (*)(uint32_t,uint32_t))(uintptr_t)callback)(event,context);}
    }
    if(finished){PENDING=0;EVENT=255;
        syscon_target_timer_unregister(ADDRESS(syscon_target_powerkey_poll));attach();}
}
void syscon_target_powerkey_debounce(uint32_t ignored){
    (void)ignored;uint32_t high=syscon_target_gpio_read(PIN);uint32_t rearm;
    if(!MODE){if(high)syscon_target_modem_key_release();else syscon_target_modem_key_assert();}
    if(high){rearm=1;if(EVENT==255){attach();return;}}
    else{
        rearm=MODE==0;
        if(EVENT==255){
            PENDING=0;PRESSED=0;RELEASED=0;FORCED=0;
            uint32_t seconds=syscon_target_modem_off()?syscon_target_powerkey_long_seconds():syscon_target_powerkey_extra_seconds();
            uint32_t ms=seconds*1000,extended=ms+5000;
            W(0x200000b8)=ms;W(0x200000c0)=ms;W(0x200000c4)=extended;W(0x200000cc)=extended;
        }
    }
    (void)syscon_target_timer_register(10,0,ADDRESS(syscon_target_powerkey_poll),0);
    if(rearm)attach();
}
int syscon_target_powerkey_callback(uint32_t function,uint32_t context){CALLBACK=function;CONTEXT=context;return 0;}
void syscon_target_powerkey_mode(uint32_t mode){
    MODE=(uint8_t)mode;
    syscon_target_logger(3,(const char *)0xcda6,(const char *)0xcd8b,(const char *)(mode?0xcd84:0xcd7b));
    syscon_target_timer_unregister(ADDRESS(syscon_target_powerkey_poll));attach();EVENT=255;
}
int syscon_target_powerkey_init(uint32_t mode){
    uint8_t configuration[12];syscon_rt_memset(configuration,0,12);configuration[5]=1;
    (void)syscon_target_gpio_config(0,(uint32_t)(uintptr_t)configuration);
    syscon_target_powerkey_mode(mode);syscon_target_timer_init();return 0;
}
