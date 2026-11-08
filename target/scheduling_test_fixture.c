/* Test-only environment; excluded from a physical-image build. No BKPT or
 * Python callback substitutions: these dependencies execute compiled ARM C. */
#include <stdint.h>
#include <stdarg.h>
#include "scheduling_target.h"
#include "runtime_memory.h"
#define V(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define B(a) (*(volatile uint8_t *)(uintptr_t)(a))
#ifdef SYSCON_SCHEDULING_PHYSICAL_FIXTURE
#define E ((volatile uint32_t *)(uintptr_t)0x20000900)
#else
#define E ((volatile uint32_t *)(uintptr_t)0x21008000)
#endif
/* E[0] event count; E[1] mode; E[2] tick entry; E[3] feed count;
 * E[4] alternate callback; E[5] callback result; E[6] logger mutation. */
static void event(uint32_t a,uint32_t b,uint32_t c,uint32_t d,uint32_t e,uint32_t f) {
    unsigned i=E[0]++;volatile uint32_t *out=E+16+6*i;
    out[0]=a;out[1]=b;out[2]=c;out[3]=d;out[4]=e;out[5]=f;
}
void syscon_target_logger(uint32_t level,const char *tag,const char *format,...) {
    uint32_t f=(uint32_t)(uintptr_t)format,args[3]={0,0,0};unsigned n=0;
    for (const char *p=format; *p; ++p) {
        if (*p!='%') continue;
        if (p[1]=='%') { ++p; continue; }
        ++n;
    }
    va_list ap;va_start(ap,format);for(unsigned i=0;i<n;++i)args[i]=va_arg(ap,uint32_t);va_end(ap);
    event(level,(uint32_t)(uintptr_t)tag,f,args[0],args[1],args[2]);
    if(E[6] && syscon_rt_strcmp(format,"Retained data raw: 0x%X 0x%X 0x%X")==0)B(0x200000da)=(uint8_t)E[6];
}
uint32_t syscon_target_watchdog_feed(void){++E[3];((void (*)(void))(uintptr_t)E[2])();return 0;}
void fixture_timer_callback(uint32_t argument) {
    uint32_t ipsr;__asm__ volatile("mrs %0, ipsr":"=r"(ipsr));E[8]=ipsr;
    event(0xf001,argument,E[1],0,0,0);
    switch(E[1]){
    case 1: V(0x20000620)=0;V(0x20000624)=0;break;
    case 2: B(0x2000061c)=1;V(0x20000620)=E[4];V(0x20000624)=99;break;
    case 3: V(0x20000640)=0;V(0x20000644)=0;V(0x20000648)=0;B(0x2000064c)=1;V(0x20000650)=E[4];V(0x20000654)=33;break;
    case 4: V(0x20000678)=0xffffffff;V(0x2000067c)=0xffffffff;break;
    default:break;
    }
}
void fixture_timer_alternate(uint32_t argument){event(0xf002,argument,0,0,0,0);}
int fixture_task_callback(void){
    event(0xf003,E[1],0,0,0,0);
    if(E[1]==1)B(0x20000595)=11;
    if(E[1]==2)B(0x20000594)=0;
    if(E[1]==3){B(0x20000600)=0;B(0x20000608)=1;}
    if(E[1]==4)((void (*)(void))(uintptr_t)E[2])();
    return (int)E[5];
}
void fixture_thread(void){for(;;){++E[7];__asm__ volatile("wfi");}}
