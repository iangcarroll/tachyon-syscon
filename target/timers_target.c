/* Physical RAM/MMIO ABI, reconstructed from 76f8..78a4. No IRQ masking:
 * even the 64-bit time read deliberately consists of low then high word. */
#include "scheduling_target.h"
#include "timers.h"
#include "runtime_memory.h"
#define WORD(a) (*(volatile uint32_t *)(uintptr_t)(a))
#define BYTE(a) (*(volatile uint8_t *)(uintptr_t)(a))
#define SLOTS ((volatile syscon_timer_slot *)(uintptr_t)0x20000610)
uint64_t syscon_target_now(void) {
    uint32_t low=WORD(0x20000678),high=WORD(0x2000067c);
    return ((uint64_t)high<<32)|low;
}
static void started_write(volatile syscon_timer_slot *s,uint64_t time) {
    volatile uint32_t *p=(volatile uint32_t *)(void *)s;
    p[0]=(uint32_t)time;p[1]=(uint32_t)(time>>32);
}
static uint64_t started_read(volatile syscon_timer_slot *s) {
    volatile uint32_t *p=(volatile uint32_t *)(void *)s;
    uint32_t low=p[0],high=p[1];return ((uint64_t)high<<32)|low;
}
void syscon_target_timer_tick(void) {
    uint64_t time=syscon_target_now()+1;
    WORD(0x20000678)=(uint32_t)time;WORD(0x2000067c)=(uint32_t)(time>>32);
    for(unsigned i=0;i<4;++i) {
        volatile syscon_timer_slot *s=&SLOTS[i];
        if(!s->callback)continue;
        uint64_t now=syscon_target_now(),start=started_read(s);
        if(now-start < s->interval)continue;
        uint32_t argument=s->argument,callback=s->callback;
        ((void (*)(uint32_t))(uintptr_t)callback)(argument);
        if(s->once){s->callback=0;s->argument=0;}
        else started_write(s,syscon_target_now());
    }
}
void syscon_target_timer_init(void) {
    if(BYTE(0x20000670))return;
    WORD(0xe000e014)=0x7cff;
    WORD(0xe000ed20)=(WORD(0xe000ed20)&0xffffff)|0xc0000000;
    WORD(0xe000e018)=0;WORD(0xe000e010)=7;
    syscon_rt_memset((void *)(uintptr_t)0x20000610,0,96);
    BYTE(0x20000670)=1;
}
int syscon_target_timer_register(uint32_t interval,uint32_t once,uint32_t callback,uint32_t argument) {
    unsigned i;for(i=0;i<4;++i)if(SLOTS[i].callback==callback)break;
    if(i==4){for(i=0;i<4;++i)if(!SLOTS[i].callback)break;if(i==4)return -1;}
    volatile syscon_timer_slot *s=&SLOTS[i];
    s->argument=argument;s->callback=callback;s->interval=interval;
    started_write(s,syscon_target_now());s->once=(uint8_t)once;return 0;
}
void syscon_target_timer_unregister(uint32_t callback) {
    for(unsigned i=0;i<4;++i)if(SLOTS[i].callback==callback){SLOTS[i].callback=0;SLOTS[i].argument=0;}
}
void syscon_target_timer_delay(uint32_t milliseconds) {
    syscon_target_logger(1,(const char *)0xdd00,(const char *)0xdce1,milliseconds);
    uint64_t start=syscon_target_now();
    while(syscon_target_now()-start < milliseconds)syscon_target_watchdog_feed();
}
void syscon_target_timer_wait_countflags(uint32_t count) {
    (void)WORD(0xe000e010);
    uint32_t elapsed=0;while(elapsed!=count)if(WORD(0xe000e010)&0x10000)++elapsed;
}
