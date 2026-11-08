/* Test-only compiled bus device and terminal assertion boundary. */
#include <stdarg.h>
#include "i2c_target.h"
#include "mspm0_core_target.h"
#include "logger_target.h"
#define E ((volatile uint32_t *)(uintptr_t)0x21008000)
#define REGS ((volatile uint8_t *)(uintptr_t)0x21008800)
static void event(uint32_t a,uint32_t b,uint32_t c,uint32_t d,uint32_t e,uint32_t f){
    volatile uint32_t *p=E+32+6*E[0]++;p[0]=a;p[1]=b;p[2]=c;p[3]=d;p[4]=e;p[5]=f;
}
void syscon_target_assert(uint32_t file,uint32_t line,uint32_t expression){
    event(0x2678,file,line,expression,0,0);E[15]=1;
    __asm__ volatile("bkpt #0");for(;;)__asm__ volatile("nop");
}
static void terminal(uint32_t entry){if(E[12]==entry)syscon_target_assert(0x1234,0x5678,entry);}
uint64_t syscon_target_i2c_init(uint32_t bus,uint32_t configuration){
    const uint8_t *p=(const uint8_t *)(uintptr_t)configuration;uint32_t lo=0,hi=0;
    for(unsigned i=0;i<4;++i){lo|=(uint32_t)p[i]<<(8*i);hi|=(uint32_t)p[i+4]<<(8*i);}
    event(0x82f0,bus,lo,hi,0,0);++E[3];terminal(0x82f0);
    if(E[6]){--E[6];return E[7];}return (uint64_t)bus<<32;
}
uint32_t syscon_target_i2c_transmit(uint32_t bus,uint32_t address,uint32_t data,uint32_t count){
    const uint8_t *p=(const uint8_t *)(uintptr_t)data;uint32_t packed=0;
    for(unsigned i=0;i<count;++i)packed|=(uint32_t)p[i]<<(8*i);
    event(0x844c,bus,address,count,packed,0);++E[1];terminal(0x844c);
    if(E[4]){--E[4];return E[7];}
    if(count)E[8]=p[0];
    for(unsigned i=1;i<count;++i)REGS[(uint8_t)(p[0]+i-1)]=p[i];
    return count;
}
uint64_t syscon_target_i2c_receive(uint32_t bus,uint32_t address,uint32_t data,uint32_t count){
    uint8_t *p=(uint8_t *)(uintptr_t)data;
    event(0x860c,bus,address,count,E[8],data>=0x20000000 && data<0x20000d00?data:0);
    ++E[2];terminal(0x860c);
    if(E[5]){--E[5];if(E[9])*p=(uint8_t)E[9];return ((uint64_t)count<<32)|E[7];}
    for(unsigned i=0;i<count;++i)p[i]=REGS[(uint8_t)(E[8]+i)];
    if(E[10]){*(volatile uint8_t *)(uintptr_t)E[10]=(uint8_t)E[11];E[10]=0;}
    return ((uint64_t)count<<32)|count;
}
uint32_t syscon_target_gpio_read(uint32_t pin){event(0x80f8,pin,0,0,0,0);return E[13];}
uint32_t syscon_target_gpio_write(uint32_t pin,uint32_t value){event(0x8054,pin,value,0,0,0);return E[14];}
void syscon_target_logger(uint32_t level,const char *tag,const char *format,...){
    va_list ap;va_start(ap,format);uint32_t pin=va_arg(ap,uint32_t);va_end(ap);
    event(0x8f88,level,(uint32_t)(uintptr_t)tag,(uint32_t)(uintptr_t)format,pin,0);
}
