/* Complete original UART parser with target callbacks and packed descriptors. */
#include "protocol_target.h"
#include "protocol_state.h"
#include "runtime_memory.h"
#include "runtime_scan.h"
#include "runtime_support.h"
#include "uart_ring_target.h"
#include "callback_helpers.h"
#include "logger_target.h"
#include <stdint.h>
#define B(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define S(a) ((const char *)(uintptr_t)(uint32_t)(a))
extern void syscon_target_logger(uint32_t, const char *, const char *, ...);
void syscon_target_protocol_poll(uint32_t context)
{
    volatile syscon_protocol_context *parser =
        (volatile syscon_protocol_context *)(uintptr_t)context;
    uint8_t uppercase[SYSCON_PROTOCOL_CAPACITY + 4];
    for (;;) {
        if (!syscon_target_uart_available(parser->port))
            return;
        uint32_t raw = syscon_target_uart_read(parser->port);
        if ((int32_t)raw < 0) {
            /* Preserve the diagnostic basename and original assertion location. */
            const char *file = "mfg_command.cpp";
            syscon_target_assert((uint32_t)(uintptr_t)file, 0x4e7,
                                 (uint32_t)(uintptr_t)"byte >= 0");
        }
        uint32_t byte = (uint8_t)raw;
        if (!parser->enabled || byte - 10u > 116)
            continue;
        if (!parser->count)
            syscon_target_logger(3, "MFGD", "");
        if (syscon_protocol_debug &&
            parser->printer != (uint32_t)(uintptr_t)syscon_target_mfg_logger)
            syscon_target_logger(1, "MFGD", "%c %d", byte, raw);
        if (parser->echo)
            syscon_target_uart_put(parser->port, byte);
        uint32_t count = parser->count;
        if (count >= SYSCON_PROTOCOL_CAPACITY - 3) {
            B(parser->buffer + SYSCON_PROTOCOL_CAPACITY - 1) = 0;
            uint32_t printer = parser->printer, buffer = parser->buffer;
            syscon_target_failure(buffer, (uint32_t)(uintptr_t)"Buffer overflow",
                                  (syscon_target_print_callback)(uintptr_t)printer);
            parser->count = 0;
            continue;
        }
        if (byte != 10 && byte != 13) {
            parser->count = count + 1;
            B(parser->buffer + count) = (uint8_t)byte;
            continue;
        }
        if (count) {
            B(parser->buffer + count) = 0;
            uint32_t buffer = parser->buffer, end = buffer;
            for (;;) {
                uint32_t c = B(end);
                if (!c)
                    break;
                if (c == ' ')
                    B(end) = ':';
                ++end;
            }
            if (end != buffer && (B(end - 1) != ';' || B(end - 2) != ':')) {
                B(end) = ':';
                B(end + 1) = ';';
                B(end + 2) = 0;
            }
            buffer = parser->buffer;
            uint32_t printer = parser->printer;
            uint32_t args = (uint32_t)(uintptr_t)syscon_rt_strchr(S(buffer), ':');
            if (args) {
                ++args;
                if (!syscon_rt_strchr(S(args), ':'))
                    args = 0;
            }
            uint32_t index;
            for (index = 0; index < syscon_target_command_count; ++index) {
                const char *name = syscon_target_commands[index].name;
                if (!syscon_rt_strncasecmp(S(buffer), name, syscon_rt_strlen(name)))
                    break;
            }
            if (index == syscon_target_command_count)
                syscon_target_failure(buffer, (uint32_t)(uintptr_t)"Unknown command",
                                      (syscon_target_print_callback)(uintptr_t)printer);
            else {
                const syscon_target_command_record *record = &syscon_target_commands[index];
                uint32_t policy = record->policy;
                if (policy == 1 && !args)
                    syscon_target_failure(buffer, (uint32_t)(uintptr_t)"Parameters required",
                                          (syscon_target_print_callback)(uintptr_t)printer);
                else if (!policy && args)
                    syscon_target_failure(buffer, (uint32_t)(uintptr_t)"No parameters required",
                                          (syscon_target_print_callback)(uintptr_t)printer);
                else {
                    if (args && record->uppercase) {
                        syscon_rt_strncpy(uppercase, S(args), SYSCON_PROTOCOL_CAPACITY - 1);
                        for (uint8_t *p = uppercase; *p; ++p)
                            *p = (uint8_t)syscon_rt_toupper(*p);
                        args = (uint32_t)(uintptr_t)uppercase;
                    }
                    uint32_t success = record->handler(args, printer);
                    ((void (*)(const char *))(uintptr_t)printer)((success ? "PASS" : "FAIL"));
                }
            }
        }
        parser->count = 0;
    }
}
