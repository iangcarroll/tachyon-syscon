#include "scheduling_target.h"
#include "runtime_memory.h"
#define TASKS ((volatile syscon_tasks *)(uintptr_t)0x20000534)
#define LOG(level,format,...) syscon_target_logger(level,(const char *)0xdc17,(const char *)(format),##__VA_ARGS__)
void syscon_target_tasks_init(void) {syscon_rt_memset((void *)TASKS,0,216);}
int syscon_target_tasks_submit(const syscon_action *actions,uint32_t count) {
    if(count>12){LOG(1,0xdc1c);return -1;}
    unsigned index=0;
    if(TASKS->slots[0].active){
        index=1;
        if(TASKS->slots[1].active){LOG(1,0xdbf6);return -1;}
    }
    volatile syscon_task *t=&TASKS->slots[index];
    syscon_rt_memcpy((void *)t->actions,actions,count*8);
    t->count=(uint8_t)count;t->current=0;t->started_ms=0;t->active=1;
    LOG(3,0xdc35,index,count);return (int)index;
}
void syscon_target_tasks_poll(void) {
    for(unsigned i=0;i<2;++i){
        volatile syscon_task *t=&TASKS->slots[i];
        if(!t->active)continue;
        uint8_t current=t->current,count=t->count;
        if(current>=count){t->active=0;continue;}
        volatile syscon_action *a=&t->actions[current];
        uint8_t kind=a->kind;
        if(kind==0){
            LOG(3,0xdc53);
            if(((int (*)(void))(uintptr_t)a->value)())++t->current;
            else {LOG(1,0xdc75);t->active=0;}
        } else if(kind==1){
            if(!t->started_ms){t->started_ms=(uint32_t)syscon_target_now();LOG(3,0xdc8d,a->value);}
            else {
                uint64_t now=syscon_target_now();uint32_t interval=a->value,start=t->started_ms;
                if(now-(uint64_t)start>=interval){LOG(3,0xdca5,interval);t->started_ms=0;++t->current;}
            }
        } else {LOG(1,0xdcbe);t->active=0;}
        current=t->current;count=t->count;
        if(current>=count){t->active=0;LOG(3,0xdcd2);}
    }
}
int syscon_target_tasks_active(void){uint8_t active=TASKS->slots[0].active;return active?active:TASKS->slots[1].active;}
