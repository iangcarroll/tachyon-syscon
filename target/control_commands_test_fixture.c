/* Test-only variadic ARM output consumer. Records the actual invocation;
 * does not sanitize user-format tokens or substitute a host printf. */
#include <stdint.h>
#include <stdarg.h>
#include "runtime_memory.h"
#define E ((volatile uint32_t *)(uintptr_t)0x21008000)
static void record(uint32_t kind,const char *format,uint32_t tag,uint32_t level,va_list args){
    uint32_t f=(uint32_t)(uintptr_t)format,count=0;
    if(f==0xb6bb || f==0xb804 || f==0xb83a || f==0xba6c)count=1;
    if(f==0xb6df || f==0xb6e7 || f==0xb939 || f==0xbab8)count=2;
    if(f==0xb8b7)count=6;
    if(E[7] && f>=0x20000000 && format[0]=='%')count=1;
    uint32_t *out=(uint32_t *)(uintptr_t)(0x21008100+E[0]++*192);
    syscon_rt_memset(out,0,192);out[0]=kind;out[1]=f<65536?f:0;out[2]=tag;out[3]=level;out[4]=count;
    for(unsigned i=0;i<count;++i)out[5+i]=va_arg(args,uint32_t);
    uint8_t *bytes=(uint8_t *)(out+16);unsigned n=0;
    while(format[n] && n<127){bytes[n]=(uint8_t)format[n];++n;}out[12]=n;
    if(E[6] && f>=0x20000000 && n<4)((char *)(uintptr_t)format)[0]='2';
}
uint32_t fixture_command_printer(const char *format,...){va_list ap;va_start(ap,format);record(1,format,0,0,ap);va_end(ap);return E[2];}
void syscon_target_logger(uint32_t level,const char *tag,const char *format,...){va_list ap;va_start(ap,format);record(2,format,(uint32_t)(uintptr_t)tag,level,ap);va_end(ap);}
void syscon_target_mfg_logger(const char *format,...){va_list ap;va_start(ap,format);record(3,format,0xb849,3,ap);va_end(ap);}
