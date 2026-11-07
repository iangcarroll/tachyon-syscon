#ifndef SYSCON_RUNTIME_HEAP_H
#define SYSCON_RUNTIME_HEAP_H
#include <stdint.h>
void *syscon_rt_malloc_r(void *,uint32_t);
void syscon_rt_free_r(void *,void *);
void *syscon_rt_realloc_r(void *,void *,uint32_t);
uint32_t syscon_rt_malloc_usable_size_r(void *,void *);
void *syscon_rt_sbrk_r(void *,int32_t);
void *syscon_rt_sbrk(int32_t);
void syscon_rt_malloc_lock(void *);
void syscon_rt_malloc_unlock(void *);
#endif
