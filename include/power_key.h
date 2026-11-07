#ifndef SYSCON_POWER_KEY_H
#define SYSCON_POWER_KEY_H
#include <stdint.h>
#include <stddef.h>
typedef struct { uint32_t start_ms, end_ms, event; } syscon_key_range;
typedef struct {
    syscon_key_range ranges[3]; /* original RAM 0x200000b4 */
    uint8_t mode, event;
    uint8_t table_padding[2];
    uint32_t pressed_ms, callback, released_ms; /* original RAM 0x20000390 */
    uint8_t release_pending, forced;
    uint8_t counter_padding[2];
    uint32_t user;
    uint16_t pin;
    uint8_t trailing_padding[2];
} syscon_power_key;
_Static_assert(offsetof(syscon_power_key, pressed_ms)==40,"key context layout");
_Static_assert(sizeof(syscon_power_key)==64,"key context size");
/* Environment calls retain original firmware addresses, explicitly not native pointers. */
typedef uint32_t (*syscon_key_call)(void *,uint32_t,uint32_t,uint32_t,uint32_t,uint32_t);
void syscon_key_edge(syscon_power_key *,uint32_t,syscon_key_call,void *);
void syscon_key_debounce(syscon_power_key *,syscon_key_call,void *);
void syscon_key_poll(syscon_power_key *,syscon_key_call,void *);
int syscon_key_register(syscon_power_key *,uint32_t,uint32_t);
void syscon_key_mode(syscon_power_key *,uint32_t,syscon_key_call,void *);
typedef void (*syscon_key_configure)(void *,uint32_t,const uint8_t *);
int syscon_key_init(syscon_power_key *,uint32_t,syscon_key_call,syscon_key_configure,void *);
#endif
