/* Concrete bindings between reconstructed target modules, never trap stubs. */
#include "fault_control_target.h"
#include "runtime_memory.h"
#include "diagnostics_target.h"
#include "uart_ring_target.h"
#include "application_target.h"
#include <stddef.h>
#include <stdint.h>
extern void syscon_target_logger(uint32_t level, const char *tag, const char *format, ...);
void *memset(void *destination, int value, size_t size) {
    _Static_assert(sizeof(size_t)==4, "ARM32 size_t required");
    return syscon_rt_memset(destination,value,(uint32_t)size);
}
_Noreturn void syscon_cfg_assert(const char *file,uint32_t line,const char *expression) {
    syscon_target_assert((uint32_t)(uintptr_t)file,line,(uint32_t)(uintptr_t)expression);
}
void syscon_core_log(uint32_t level,const char *tag,const char *message) {
    (void)syscon_target_logger(level,tag,message);
}

void *memcpy(void *destination,const void *source,size_t size) {
    return syscon_rt_memcpy(destination,source,(uint32_t)size);
}
void syscon_target_uart_write(unsigned port,const uint8_t *buffer,uint32_t length) {
    if(port==0)syscon_target_diagnostic_write((uint32_t)(uintptr_t)buffer,length);
    else (void)syscon_target_uart_write_buffer(port,(uint32_t)(uintptr_t)buffer,length);
}
int syscon_target_color(void) {return (int)syscon_target_log_color();}
