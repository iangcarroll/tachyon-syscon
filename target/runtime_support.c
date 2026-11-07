#include "runtime_support.h"
extern int32_t syscon_rt_strtol(const char *,char **,int32_t);
#include "runtime_stdio.h"
/* The pinned image's unresolved weak __register_exitproc is zero. No callback
 * registration takes place, regardless of the supplied arguments. */
int syscon_rt_cxa_atexit(void (*fn)(void *),void *arg,void *dso) {
    (void)fn;(void)arg;(void)dso;return 0;
}
int syscon_rt_arm_atexit(void *arg,void (*fn)(void *),void *dso) {
    return syscon_rt_cxa_atexit(fn,arg,dso);
}
int32_t syscon_rt_atoi(const char *text) {return syscon_rt_strtol(text,0,10);}
int syscon_rt_isalnum(int32_t character) {
    return *(const uint8_t *)(uintptr_t)(0xe127u+(uint32_t)character)&7;
}
int32_t syscon_rt_toupper(int32_t character) {
    uint8_t flags=*(const uint8_t *)(uintptr_t)(0xe127u+(uint32_t)character);
    return (flags&3)==2 ? (int32_t)((uint32_t)character-32u) : character;
}
uint8_t *syscon_rt_getreent(void) {
    return (uint8_t *)(uintptr_t)*(volatile uint32_t *)(uintptr_t)0x20000258;
}
uint32_t syscon_rt_strtoul_alias(void *reent,const char *text,char **end,int32_t base) {
    return syscon_rt_strtoul_r(reent,text,end,base);
}
void syscon_rt_lock_acquire(uint32_t *lock) {(void)lock;}
void syscon_rt_lock_release(uint32_t *lock) {(void)lock;}
void *syscon_rt_memmove(void *destination,const void *source,uint32_t size) {
    uint8_t *d=destination;const uint8_t *s=source;
    uint32_t to=(uint32_t)(uintptr_t)d,from=(uint32_t)(uintptr_t)s;
    if(from<to && to<from+size){while(size){--size;d[size]=s[size];}}
    else for(uint32_t i=0;i<size;++i)d[i]=s[i];
    return destination;
}
