#ifndef SYSCON_APPLICATION_STATE_H
#define SYSCON_APPLICATION_STATE_H
#include <stdint.h>
#include "protocol_state.h"

enum { SYSCON_KEY_QUEUE_CAPACITY = 4 };
/* Address words preserve ARM32 wrap and callback aliasing behavior. */
typedef struct {
    uint32_t buffer, capacity, write, read;
    uint8_t full;
    uint8_t reserved[3];
} syscon_event_queue;
_Static_assert(sizeof(syscon_event_queue) == 20, "Event queue layout");
extern volatile syscon_event_queue syscon_key_events;
extern volatile uint8_t syscon_key_event_buffer[SYSCON_KEY_QUEUE_CAPACITY];
extern volatile uint8_t syscon_shutdown_pending, syscon_key_started_off;
extern volatile uint8_t syscon_wakeup_pending;
extern uint8_t syscon_application_dso;
extern volatile syscon_protocol_context syscon_console_parser;
extern volatile uint8_t syscon_console_buffer[SYSCON_PROTOCOL_CAPACITY];
#endif
