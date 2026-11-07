#ifndef SYSCON_POWER_KEY_TARGET_H
#define SYSCON_POWER_KEY_TARGET_H
#include <stdint.h>
int syscon_target_powerkey_edge(uint32_t pin);          /* 570c */
void syscon_target_powerkey_poll(uint32_t ignored);     /* 5740 */
void syscon_target_powerkey_debounce(uint32_t ignored); /* 5844 */
int syscon_target_powerkey_callback(uint32_t function,uint32_t context); /* 5908 */
void syscon_target_powerkey_mode(uint32_t mode);        /* 591c */
int syscon_target_powerkey_init(uint32_t mode);         /* 5970 */
uint32_t syscon_target_modem_off(void);                 /* 6690 */
void syscon_target_modem_key_assert(void);              /* 6a28 */
void syscon_target_modem_key_release(void);             /* 6a48 */
#endif
