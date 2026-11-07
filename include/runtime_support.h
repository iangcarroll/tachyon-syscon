#ifndef SYSCON_RUNTIME_SUPPORT_H
#define SYSCON_RUNTIME_SUPPORT_H
#include <stdint.h>
int syscon_rt_cxa_atexit(void (*fn)(void *),void *arg,void *dso);
int syscon_rt_arm_atexit(void *arg,void (*fn)(void *),void *dso);
int32_t syscon_rt_atoi(const char *text);
int syscon_rt_isalnum(int32_t character);
int32_t syscon_rt_toupper(int32_t character);
uint8_t *syscon_rt_getreent(void);
uint32_t syscon_rt_strtoul_alias(void *reent,const char *text,char **end,int32_t base);
void syscon_rt_lock_acquire(uint32_t *lock);
void syscon_rt_lock_release(uint32_t *lock);
void *syscon_rt_memmove(void *destination,const void *source,uint32_t size);
#endif
