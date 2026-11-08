#ifndef SYSCON_RUNTIME_STATE_H
#define SYSCON_RUNTIME_STATE_H
#include <stdint.h>

/* The image contains three zero-filled 32-byte stdio placeholders. The
 * recovered routines use explicit caller-supplied FILEs; these are not live
 * UART streams and must not be mistaken for an initialized stdio driver. */
typedef struct {
    uint32_t unused[8];
} syscon_stdio_placeholder;
typedef struct {
    int32_t error;
    const syscon_stdio_placeholder *input, *output, *error_output;
    /* Unused trailing newlib context storage retained from this image. */
    uint32_t reserved[21];
} syscon_runtime_context_t;
_Static_assert(sizeof(syscon_runtime_context_t) == 100, "Runtime context layout");
extern syscon_runtime_context_t syscon_runtime_context;
extern syscon_runtime_context_t *volatile syscon_runtime_current;
extern const syscon_stdio_placeholder syscon_stdio_input, syscon_stdio_output, syscon_stdio_error;

typedef struct {
    uint32_t error, lock, free_head, heap_start;
} syscon_heap_state;
extern syscon_heap_state syscon_runtime_heap;
#endif
