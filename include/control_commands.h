#ifndef SYSCON_CONTROL_COMMANDS_H
#define SYSCON_CONTROL_COMMANDS_H
#include <stdint.h>
#include "syscon.h"

typedef struct {
    uint32_t is_string;
    uint32_t number;
    const char *string;
} syscon_control_arg;
typedef struct {
    void *context;
    int32_t (*call)(void *, uint32_t original_address, uint32_t a, uint32_t b,
                    uint8_t *data, uint32_t size);
    void (*print)(void *, const char *format, const syscon_control_arg *, unsigned count);
    void (*log)(void *, unsigned level, const char *tag, const char *format,
                const syscon_control_arg *, unsigned count);
    uint8_t debug_enabled;
} syscon_control_io;
#define SYSCON_CONTROL_TERMINATED INT32_MIN
#define SYSCON_CONTROL_UNHANDLED (INT32_MIN + 1)
/* Format calls are preserved, including SET_RGB's unsafe user format strings.
 * TERMINATED means reset/assertion never returned in the original image.
 * The caller MUST stop dispatch; it is not a normal nonzero/PASS result. */
int32_t syscon_control_command(syscon_control_io *, uint32_t handler, const char *arguments);
/* Host harness: stop the parser at non-returning commands; fallback connects
 * reconstructed CONFIG handlers. Returns 0, TERMINATED, or UNHANDLED. */
int32_t syscon_control_feed(syscon_control_io *, syscon_parser *, const uint8_t *, size_t,
                            syscon_dispatch fallback, void *fallback_context,
                            syscon_echo echo, void *echo_context);
#endif
