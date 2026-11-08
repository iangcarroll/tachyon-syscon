#include "runtime_state.h"

const syscon_stdio_placeholder syscon_stdio_input = {0};
const syscon_stdio_placeholder syscon_stdio_output = {0};
const syscon_stdio_placeholder syscon_stdio_error = {0};
syscon_runtime_context_t syscon_runtime_context
    __attribute__((section(".data.syscon_runtime_context"))) = {
        .input = &syscon_stdio_input,
        .output = &syscon_stdio_output,
        .error_output = &syscon_stdio_error,
};
syscon_runtime_context_t *volatile syscon_runtime_current
    __attribute__((section(".data.syscon_runtime_current"))) = &syscon_runtime_context;
syscon_heap_state syscon_runtime_heap __attribute__((section(".bss.syscon_runtime_heap")));
