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
static void store32(uint8_t *p, uint32_t value)
{
    *(uint32_t *)p = value;
}
uint32_t syscon_logger_target_vformat(uint8_t *out, uint32_t capacity, const char *format,
                                      uint32_t args)
{
    return syscon_vformat_target(out, capacity, (uint32_t)(uintptr_t)format, args).length;
}
void syscon_logger_target_body(uint8_t *frame, uint32_t level, const char *tag, const char *format,
                               uint32_t args)
{
    if (syscon_target_color()) {
        static const char *const colors[] = {"", "\033[0;31m", "\033[0;33m", "\033[0;37m",
                                             "\033[0;34m"};
        if (level >= 1 && level <= 4)
            syscon_target_uart_write(0, (const uint8_t *)colors[level], 7);
    }
    uint64_t now = syscon_target_now();
    store32(frame, (uint32_t)now);
    store32(frame + 4, (uint32_t)(now >> 32));
    store32(frame + 8, (uint32_t)(uintptr_t)tag);
    uint32_t length =
        syscon_logger_target_vformat(frame + 24, 32, "[%lld] [%s] ", (uint32_t)(uintptr_t)frame);
    syscon_target_uart_write(0, frame + 24, length);
    store32(frame + 16, args);
    length = syscon_logger_target_vformat(frame + 56, 32, format, args);
    uint8_t *message = frame + 56;
    if (length - 1u > 30) {
        store32(frame + 16, args);
        length = syscon_logger_target_vformat(frame + 88, 256, format, args);
        if ((int32_t)length <= 0)
            goto suffix;
        if ((int32_t)length > 255) {
            store32(frame + 20, 0x002e2e2e);
            syscon_rt_memcpy(frame + 340, frame + 20, 3);
            frame[343] = 0;
            length = 255;
        }
        message = frame + 88;
    }
    syscon_target_uart_write(0, message, length);
suffix:
    if (syscon_target_color())
        syscon_target_uart_write(0, (const uint8_t *)"\033[0m", 4);
    syscon_rt_memcpy(frame + 88, "\r\n", 3);
    /* Final UART call is in the ASM adapter, preserving its R0-R3 outputs. */
}
void syscon_logger_target_sg_body(uint8_t *frame, const char *format, uint32_t args)
{
    store32(frame + 4, args);
    syscon_rt_memset(frame + 8, 0, 128);
    syscon_logger_target_vformat(frame + 8, 128, format, args);
    uint32_t length = syscon_rt_strlen(frame + 8);
    syscon_target_uart_write(1, frame + 8, length);
    syscon_rt_memcpy(frame, "\r\n", 3);
    syscon_target_uart_write(1, frame, 2);
}
