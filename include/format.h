#ifndef SYSCON_FORMAT_H
#define SYSCON_FORMAT_H
#include <stdint.h>
typedef struct { int (*read_byte)(void *,uint32_t,uint8_t *);void *ctx; } syscon_format_memory;
typedef struct { uint32_t length,next_argument;int complete; } syscon_format_result;
/* Explicit target-memory va_list keeps 32-bit pointers and 8-byte alignment. */
syscon_format_result syscon_vformat(uint8_t *,uint32_t,uint32_t,uint32_t,const syscon_format_memory *);
typedef struct {
    void *ctx;
    void (*write)(void *,unsigned,const uint8_t *,uint32_t);
    uint64_t (*now)(void *);
    int (*color)(void *);
} syscon_log_io;
int syscon_sg560d_printf(const syscon_format_memory *,const syscon_log_io *,uint32_t,uint32_t);
/* Returns -2 for the original logger's prefix-buffer overread boundary. */
int syscon_logger(const syscon_format_memory *,const syscon_log_io *,uint8_t,uint32_t,uint32_t,uint32_t,uint32_t);
/* Original callback-output context at 0x9028: target callback pointer, user
 * context, and a wrapping count incremented before invoking the callback. */
typedef struct { uint32_t callback,context,count; } syscon_format_target_output;
typedef void (*syscon_format_call)(void *,uint32_t callback,uint32_t character,uint32_t context);
void syscon_format_forward(syscon_format_target_output *,uint32_t,syscon_format_call,void *);
/* Generic 0x9038 callback formatter: emits every byte, including embedded NUL,
 * but no trailing terminator. call must be non-NULL. */
syscon_format_result syscon_vformat_callback(uint32_t,uint32_t,syscon_format_call,void *,
    uint32_t,uint32_t,const syscon_format_memory *);
/* Native ARM address-space access, preserving byte/word load widths. */
syscon_format_result syscon_vformat_target(uint8_t *,uint32_t,uint32_t,uint32_t);
#endif
