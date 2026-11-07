/* Original nano allocator, target32 pointer layout and globals preserved. */
#include "runtime_heap.h"
#include "runtime_memory.h"
#include <stdint.h>
#define P(a) ((uint32_t *)(uintptr_t)(uint32_t)(a))
#define U(p) ((uint32_t)(uintptr_t)(p))
#define FREE_HEAD (*P(0x20000818))
#define HEAP_START (*P(0x2000081c))
#define GLOBAL_ERRNO (*P(0x20000810))
extern void syscon_rt_lock_acquire(uint32_t *);
extern void syscon_rt_lock_release(uint32_t *);
void syscon_rt_malloc_lock(void *reent) {(void)reent;syscon_rt_lock_acquire(P(0x20000814));}
void syscon_rt_malloc_unlock(void *reent) {(void)reent;syscon_rt_lock_release(P(0x20000814));}
/* The actual image's weak sbrk endpoint0x76f0 always returns -1. Tests may
 * replace this explicit endpoint with a scripted backing store. */
__attribute__((weak,noinline)) void *syscon_rt_sbrk(int32_t increment) {(void)increment;return (void *)(uintptr_t)UINT32_MAX;}
void *syscon_rt_sbrk_r(void *reent,int32_t increment) {
    GLOBAL_ERRNO=0;
    void *result=syscon_rt_sbrk(increment);
    if(U(result)==UINT32_MAX && GLOBAL_ERRNO)*(uint32_t *)reent=GLOBAL_ERRNO;
    return result;
}
uint32_t syscon_rt_malloc_usable_size_r(void *reent,void *memory) {
    (void)reent;uint32_t p=U(memory),header=*P(p-4),size=header-4;
    if((int32_t)header<0)size+=*P(p+size);
    return size;
}
void syscon_rt_free_r(void *reent,void *memory) {
    if(!memory)return;
    uint32_t block=U(memory)-4;
    if((int32_t)*P(block)<0)block+=*P(block);
    syscon_rt_malloc_lock(reent);
    uint32_t next=FREE_HEAD;
    if(next && next<=block) {
        uint32_t prev;
        do {prev=next;next=P(prev)[1];}while(next && next<=block);
        uint32_t end=prev+*P(prev);
        if(end==block) {
            *P(prev)+=*P(block);
            if(next==prev+*P(prev)) {*P(prev)+=*P(next);P(prev)[1]=P(next)[1];}
        } else if(block<end) *(uint32_t *)reent=12;
        else {
            if(next==block+*P(block)){*P(block)+=*P(next);next=P(next)[1];}
            P(block)[1]=next;P(prev)[1]=block;
        }
    } else {
        if(next && next==block+*P(block)){*P(block)+=*P(next);next=P(next)[1];}
        P(block)[1]=next;FREE_HEAD=block;
    }
    syscon_rt_malloc_unlock(reent);
}
void *syscon_rt_malloc_r(void *reent,uint32_t requested) {
    uint32_t size=((requested+3)&~UINT32_C(3))+8;
    if(size<12)size=12;
    else if((int32_t)size<0)goto fail;
    if(requested>size)goto fail;
    syscon_rt_malloc_lock(reent);
    uint32_t previous=FREE_HEAD,block=FREE_HEAD;
    while(block) {
        uint32_t left=*P(block)-size;
        if((int32_t)left>=0) {
            if(left>11) {*P(block)=left;block+=left;*P(block)=size;}
            else if(previous==block)FREE_HEAD=P(block)[1];
            else P(previous)[1]=P(block)[1];
            goto found;
        }
        previous=block;block=P(block)[1];
    }
    if(!HEAP_START)HEAP_START=U(syscon_rt_sbrk_r(reent,0));
    uint32_t raw=U(syscon_rt_sbrk_r(reent,(int32_t)size));
    if(raw==UINT32_MAX)goto unlock_fail;
    block=(raw+3)&~UINT32_C(3);
    if(raw!=block && U(syscon_rt_sbrk_r(reent,(int32_t)(block-raw)))==UINT32_MAX)goto unlock_fail;
    *P(block)=size;
found:
    syscon_rt_malloc_unlock(reent);
    uint32_t result=(block+11)&~UINT32_C(7);
    if(result!=block+4)*P(result-4)=block+4-result;
    return (void *)(uintptr_t)result;
unlock_fail:
    *(uint32_t *)reent=12;syscon_rt_malloc_unlock(reent);return 0;
fail:
    *(uint32_t *)reent=12;return 0;
}
void *syscon_rt_realloc_r(void *reent,void *memory,uint32_t size) {
    if(!memory)return syscon_rt_malloc_r(reent,size);
    if(!size){syscon_rt_free_r(reent,memory);return 0;}
    if(syscon_rt_malloc_usable_size_r(reent,memory)>=size)return memory;
    void *result=syscon_rt_malloc_r(reent,size);
    if(result){
        /* Original copies the requested NEW size, even beyond the old chunk. */
        syscon_rt_memcpy(result,memory,size);syscon_rt_free_r(reent,memory);
    }
    return result;
}
