/* Test-only compiled external environment, not part of a physical image. */
#include <stdarg.h>
#include "power_key_target.h"
#include "scheduling_target.h"
#include "mspm0_core_target.h"
#include "diagnostics_target.h"
#include "runtime_memory.h"
#define E ((volatile uint32_t *)(uintptr_t)0x21008000)
#define B(a) (*(volatile uint8_t *)(uintptr_t)(a))
#define W(a) (*(volatile uint32_t *)(uintptr_t)(a))
static void event(uint32_t a,uint32_t b,uint32_t c,uint32_t d,uint32_t e,uint32_t f){
    volatile uint32_t *p=E+16+6*E[0]++;p[0]=a;p[1]=b;p[2]=c;p[3]=d;p[4]=e;p[5]=f;
}
void syscon_target_logger(uint32_t level,const char *tag,const char *format,...){
    va_list ap;va_start(ap,format);uint32_t argument=va_arg(ap,uint32_t);va_end(ap);
    event(0x8f88,level,(uint32_t)(uintptr_t)tag,(uint32_t)(uintptr_t)format,argument,0);
}
uint32_t syscon_target_watchdog_feed(void){++E[3];((void (*)(void))(uintptr_t)E[2])();return 0;}
uint32_t syscon_target_gpio_read(uint32_t pin){event(0x80f8,pin,0,0,0,0);return E[1];}
uint32_t syscon_target_gpio_detach(uint32_t pin){event(0x81f8,pin,0,0,0,0);return 0;}
uint64_t syscon_target_gpio_attach(uint32_t pin,uint32_t edge,uint32_t callback,uint32_t context){event(0x8148,pin,edge,callback,context,0);return (uint64_t)pin<<32;}
uint32_t syscon_target_gpio_config(uint32_t pin,uint32_t config){
    const uint8_t *p=(const uint8_t *)(uintptr_t)config;uint32_t words[3];syscon_rt_memset(words,0,sizeof(words));
    for(unsigned i=0;i<12;++i)words[i/4]|=(uint32_t)p[i]<<(8*(i%4));
    event(0x7f58,pin,words[0],words[1],words[2],0);return 0;
}
uint32_t syscon_target_modem_off(void){event(0x6690,0,0,0,0,0);return E[5];}
void syscon_target_modem_key_assert(void){event(0x6a28,0,0,0,0,0);if(E[4])B(0x200000d8)=(uint8_t)E[4];}
void syscon_target_modem_key_release(void){event(0x6a48,0,0,0,0,0);if(E[4])B(0x200000d8)=(uint8_t)E[4];}
uint32_t syscon_target_edl_timer_seconds(void){event(0x315c,0,0,0,0,0);return E[6];}
uint32_t syscon_target_shutdown_timer_seconds(void){event(0x3178,0,0,0,0,0);return E[7];}
void fixture_key_callback(uint32_t key_event,uint32_t context){
    event(0xf100,key_event,context,0,0,0);++E[9];
    if(E[8]==1){B(0x200000d9)=42;B(0x2000039c)=0;}
    if(E[8]==2){W(0x20000394)=0;W(0x200003a0)=1234;}
    if(E[8]==3){B(0x200000d8)=1;W(0x20000390)=0;W(0x20000398)=0;}
}
void fixture_unused_timer(uint32_t value){event(0xf101,value,0,0,0,0);}
