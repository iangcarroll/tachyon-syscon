#ifndef SYSCON_FORMAT_CORE_TARGET_H
#define SYSCON_FORMAT_CORE_TARGET_H
#include <stdint.h>
/* 8fcc: low result=count, high result=original buffer pointer. Digits reversed. */
uint64_t syscon_target_format_digits(uint64_t value,uint32_t buffer,uint32_t radix,uint32_t alphabet_offset);
uint32_t syscon_target_format_forward(uint32_t character,uint32_t context); /* 9028 */
uint32_t syscon_target_vformat_callback(uint32_t callback,uint32_t context,uint32_t format,uint32_t arguments); /* 9038 */
#endif
