#ifndef SYSCON_RUNTIME_SUPPORT_H
#define SYSCON_RUNTIME_SUPPORT_H
#include <stdint.h>
int syscon_rt_cxa_atexit(void (*fn)(void *),void *arg,void *dso);
int syscon_rt_arm_atexit(void *arg,void (*fn)(void *),void *dso);
int32_t syscon_rt_atoi(const char *text);
/* C-locale flags used by the recovered scan routines. Inputs outside the
 * unsigned-byte/EOF domain have no character flags. */
enum {
    SYSCON_CTYPE_UPPER = 1, SYSCON_CTYPE_LOWER = 2, SYSCON_CTYPE_DIGIT = 4,
    SYSCON_CTYPE_SPACE = 8, SYSCON_CTYPE_PUNCT = 16, SYSCON_CTYPE_CONTROL = 32,
    SYSCON_CTYPE_HEX = 64, SYSCON_CTYPE_BLANK = 128
};
uint8_t syscon_rt_ctype(int32_t character);
int syscon_rt_isalnum(int32_t character);
int32_t syscon_rt_toupper(int32_t character);
uint8_t *syscon_rt_getreent(void);
uint32_t syscon_rt_strtoul_alias(void *reent,const char *text,char **end,int32_t base);
void syscon_rt_lock_acquire(uint32_t *lock);
void syscon_rt_lock_release(uint32_t *lock);
void *syscon_rt_memmove(void *destination,const void *source,uint32_t size);
#endif
