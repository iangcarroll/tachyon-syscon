/* Standalone original AAPCS entrypoints; no host callback/context adapters. */
#include "callback_helpers.h"
#include <stddef.h>
_Static_assert(sizeof(void *) == 4, "ARM32 target required");
_Static_assert(sizeof(syscon_target_output_buffer) == 12, "original output layout");
_Static_assert(offsetof(syscon_target_output_buffer, used) == 8, "original used offset");

uint32_t syscon_target_failure(uint32_t command, uint32_t reason,
                              syscon_target_print_callback print) {
    if (command) print(command);
    print(reason);
    /* Response text belongs to this image and moves with the source. */
    return print((uint32_t)(uintptr_t)"FAIL");
}

uint32_t syscon_target_buffer_output(uint32_t character,
                                    volatile syscon_target_output_buffer *output) {
    /* Volatile order matters when output storage aliases its own context. */
    uint32_t used = output->used;
    uint32_t capacity = output->capacity;
    if (used < capacity) {
        uint32_t buffer = output->buffer;
        output->used = used + UINT32_C(1);
        *(volatile uint8_t *)(uintptr_t)(buffer + used) = (uint8_t)character;
    }
    return character;
}

uint32_t syscon_target_null_output(uint32_t character, uint32_t context) {
    (void)context;
    return character;
}
