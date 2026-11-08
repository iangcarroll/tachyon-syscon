#ifndef SYSCON_PROTOCOL_STATE_H
#define SYSCON_PROTOCOL_STATE_H
#include <stdint.h>
enum { SYSCON_PROTOCOL_CAPACITY = 128 };
/* The parser accesses these fields through volatile references because UART
 * callbacks can change echo, enable, count or buffer while it is polling.
 * Address words retain ARM32 wrap behavior for the recovered callback ABI. */
typedef struct {
    uint8_t port;
    uint8_t reserved[3];
    uint32_t buffer;
    uint32_t count;
    uint8_t echo, enabled;
    uint8_t padding[2];
    uint32_t printer;
} syscon_protocol_context;
_Static_assert(sizeof(syscon_protocol_context) == 20, "UART parser context ABI");
/* Raw modem RX diagnostics; changed by the 560D_DBG command. */
extern volatile uint8_t syscon_protocol_debug;
#endif
