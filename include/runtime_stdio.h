#ifndef SYSCON_RUNTIME_STDIO_H
#define SYSCON_RUNTIME_STDIO_H
#include <stdint.h>
typedef int (*syscon_rt_writer)(void *,void *,const char *,uint32_t);
uint32_t syscon_rt_strtoul_r(void *,const char *,char **,int);
int syscon_rt_swrite(void *,void *,const char *,uint32_t);
int syscon_rt_sungetc_r(void *,int,void *);
int syscon_rt_ssrefill_r(void *,void *);
int syscon_rt_submore(void *,void *);
int syscon_rt_printf_common(void *,void *,int32_t *,void *,syscon_rt_writer);
int syscon_rt_printf_integer(void *,void *,void *,syscon_rt_writer,void *);
#endif
