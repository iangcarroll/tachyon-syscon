#ifndef SYSCON_LOGGER_FRAME_H
#define SYSCON_LOGGER_FRAME_H

/* Shared C/assembly layout of the legacy buffers exposed by prefix overreads.
 * These are stack offsets, never addresses in a particular firmware image. */
#define SYSCON_LOG_PREFIX_CAPACITY 32
#define SYSCON_LOG_SHORT_CAPACITY 32
#define SYSCON_LOG_MESSAGE_CAPACITY 256
#define SYSCON_LOG_PREFIX_OFFSET 24
#define SYSCON_LOG_SHORT_OFFSET (SYSCON_LOG_PREFIX_OFFSET + SYSCON_LOG_PREFIX_CAPACITY)
#define SYSCON_LOG_MESSAGE_OFFSET (SYSCON_LOG_SHORT_OFFSET + SYSCON_LOG_SHORT_CAPACITY)
#define SYSCON_LOG_FRAME_SIZE (SYSCON_LOG_MESSAGE_OFFSET + SYSCON_LOG_MESSAGE_CAPACITY + 4)
#define SYSCON_LOG_CALL_ARGS_SIZE 8
#define SYSCON_LOG_SUFFIX_OFFSET (SYSCON_LOG_MESSAGE_OFFSET + SYSCON_LOG_CALL_ARGS_SIZE)
#define SYSCON_SG_MESSAGE_CAPACITY 128
#define SYSCON_SG_FRAME_SIZE (8 + SYSCON_SG_MESSAGE_CAPACITY)

#ifndef __ASSEMBLER__
#include <stddef.h>
#include <stdint.h>

typedef struct {
    uint32_t timestamp_low, timestamp_high;
    uint32_t tag;
    uint32_t unused;
    uint32_t arguments;
    uint8_t ellipsis[4];
    uint8_t prefix[SYSCON_LOG_PREFIX_CAPACITY];
    uint8_t short_message[SYSCON_LOG_SHORT_CAPACITY];
    uint8_t message[SYSCON_LOG_MESSAGE_CAPACITY];
    uint32_t padding;
} syscon_logger_frame;

typedef struct {
    uint8_t newline[4];
    uint32_t arguments;
    uint8_t message[SYSCON_SG_MESSAGE_CAPACITY];
} syscon_sg_logger_frame;

_Static_assert(offsetof(syscon_logger_frame, prefix) == SYSCON_LOG_PREFIX_OFFSET, "prefix ABI");
_Static_assert(offsetof(syscon_logger_frame, short_message) == SYSCON_LOG_SHORT_OFFSET, "short ABI");
_Static_assert(offsetof(syscon_logger_frame, message) == SYSCON_LOG_MESSAGE_OFFSET, "message ABI");
_Static_assert(sizeof(syscon_logger_frame) == SYSCON_LOG_FRAME_SIZE, "logger frame ABI");
_Static_assert(sizeof(syscon_sg_logger_frame) == SYSCON_SG_FRAME_SIZE, "modem logger frame ABI");
#endif
#endif
