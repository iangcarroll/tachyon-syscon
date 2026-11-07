#ifndef SYSCON_IOEXPANDER_TARGET_H
#define SYSCON_IOEXPANDER_TARGET_H
#include <stdint.h>
#include "ioexpander.h"
uint32_t syscon_target_pin_read(uint32_t pin);          /* 3620 */
uint32_t syscon_target_pin_write(uint32_t pin,uint32_t value); /* 364e */
uint32_t syscon_target_ioexpander_write16(uint32_t reg,uint32_t value); /* 3668 */
uint32_t syscon_target_ioexpander_read8(uint32_t reg,uint8_t *value); /* 36bc */
uint32_t syscon_target_ioexpander_write8(uint32_t reg,uint32_t value); /* 374c */
int syscon_target_ioexpander_write_unchecked(uint32_t pin,uint32_t value); /* 379c */
uint32_t syscon_target_ioexpander_reset(void);           /* 37e4 */
int syscon_target_ioexpander_init(uint32_t cold);        /* 3808 */
int syscon_target_ioexpander_configure(uint32_t pin,const syscon_io_config *configuration); /* 386c */
int syscon_target_ioexpander_write(uint32_t pin,uint32_t value); /* 3940 */
int syscon_target_ioexpander_read(uint32_t pin,uint8_t *value); /* 39e8 */
#endif
