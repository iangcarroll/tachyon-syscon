#ifndef SYSCON_RUNTIME_MEMORY_H
#define SYSCON_RUNTIME_MEMORY_H
#include <stdint.h>
int syscon_rt_strcmp(const void *left,const void *right);
uint32_t syscon_rt_strlen(const void *text);
int syscon_rt_memcmp(const void *left,const void *right,uint32_t size);
void *syscon_rt_memcpy(void *destination,const void *source,uint32_t size);
void *syscon_rt_memset(void *destination,int value,uint32_t size);
void *syscon_rt_strchr(const void *text,int value);
int syscon_rt_strncmp(const void *left,const void *right,uint32_t size);
void *syscon_rt_strncpy(void *destination,const void *source,uint32_t size);
void *syscon_rt_strrchr(const void *text,int value);
void *syscon_rt_memchr(const void *data,int value,uint32_t size);
#endif
