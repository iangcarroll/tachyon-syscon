/* Preserve the original logger's exposed target frame; do not cap the UART
 * prefix length to its 32-byte buffer. The frame is reserved by ARM ABI glue. */
#include "logger_target.h"
#include "logger_state.h"
#include "format.h"
#include "runtime_memory.h"
#include <stdint.h>
extern void syscon_target_uart_write(unsigned, const uint8_t *, uint32_t);
extern uint64_t syscon_target_now(void);
extern int syscon_target_color(void);
uint32_t syscon_logger_target_vformat(uint8_t *out, uint32_t capacity, const char *format,
                                      uint32_t args)
{
    return syscon_vformat_target(out, capacity, (uint32_t)(uintptr_t)format, args).length;
}
void syscon_logger_target_body(syscon_logger_frame *frame, uint32_t level, const char *tag,
                               const char *format, uint32_t args)
{
    if (syscon_target_color()) {
        static const char *const colors[] = {"", "\033[0;31m", "\033[0;33m", "\033[0;37m",
                                             "\033[0;34m"};
        if (level >= 1 && level <= 4)
            syscon_target_uart_write(0, (const uint8_t *)colors[level], 7);
    }
    uint64_t now = syscon_target_now();
    frame->timestamp_low = (uint32_t)now;
    frame->timestamp_high = (uint32_t)(now >> 32);
    frame->tag = (uint32_t)(uintptr_t)tag;
    uint32_t length = syscon_logger_target_vformat(frame->prefix, sizeof(frame->prefix),
                                                   "[%lld] [%s] ", (uint32_t)(uintptr_t)frame);
    syscon_target_uart_write(0, frame->prefix, length);
    frame->arguments = args;
    length = syscon_logger_target_vformat(frame->short_message, sizeof(frame->short_message),
                                          format, args);
    uint8_t *message = frame->short_message;
    if (length - 1u > sizeof(frame->short_message) - 2) {
        frame->arguments = args;
        length = syscon_logger_target_vformat(frame->message, sizeof(frame->message), format, args);
        if ((int32_t)length <= 0)
            goto suffix;
        if ((int32_t)length >= (int32_t)sizeof(frame->message)) {
            *(uint32_t *)frame->ellipsis = 0x002e2e2e;
            syscon_rt_memcpy(frame->message + sizeof(frame->message) - 4, frame->ellipsis, 3);
            frame->message[sizeof(frame->message) - 1] = 0;
            length = sizeof(frame->message) - 1;
        }
        message = frame->message;
    }
    syscon_target_uart_write(0, message, length);
suffix:
    if (syscon_target_color())
        syscon_target_uart_write(0, (const uint8_t *)"\033[0m", 4);
    syscon_rt_memcpy(frame->message, "\r\n", 3);
    /* Final UART call is in the ASM adapter, preserving its R0-R3 outputs. */
}
void syscon_logger_target_sg_body(syscon_sg_logger_frame *frame, const char *format, uint32_t args)
{
    frame->arguments = args;
    syscon_rt_memset(frame->message, 0, sizeof(frame->message));
    syscon_logger_target_vformat(frame->message, sizeof(frame->message), format, args);
    uint32_t length = syscon_rt_strlen(frame->message);
    syscon_target_uart_write(1, frame->message, length);
    syscon_rt_memcpy(frame->newline, "\r\n", 3);
    syscon_target_uart_write(1, frame->newline, 2);
}
