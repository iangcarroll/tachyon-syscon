#ifndef SYSCON_CALLBACK_HELPERS_H
#define SYSCON_CALLBACK_HELPERS_H
#include <stdint.h>
typedef struct {
    uint32_t buffer;
    uint32_t capacity;
    uint32_t used;
} syscon_target_output_buffer;
typedef uint32_t (*syscon_target_print_callback)(uint32_t string_address);
uint32_t syscon_target_failure(uint32_t command, uint32_t reason,
                              syscon_target_print_callback print);
uint32_t syscon_target_buffer_output(uint32_t character,
                                    volatile syscon_target_output_buffer *output);
uint32_t syscon_target_null_output(uint32_t character, uint32_t context);
#endif
