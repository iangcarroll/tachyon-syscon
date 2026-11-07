#ifndef SYSCON_RUNTIME_ARITHMETIC_H
#define SYSCON_RUNTIME_ARITHMETIC_H
#include <stdint.h>
uint32_t syscon_rt_clz32(uint32_t value);
uint32_t syscon_rt_clz64(uint64_t value);
uint64_t syscon_rt_udiv32(uint32_t numerator,uint32_t denominator);
uint64_t syscon_rt_idiv32(uint32_t numerator,uint32_t denominator);
uint64_t syscon_rt_mul64(uint64_t left,uint64_t right);
uint64_t syscon_rt_udiv64(uint64_t numerator,uint64_t denominator,uint64_t *remainder);
int syscon_rt_fcmp_low(uint32_t left,uint32_t right);
int syscon_rt_fcmp_high(uint32_t left,uint32_t right);
int syscon_rt_dcmp_low(uint64_t left,uint64_t right);
int syscon_rt_dcmp_high(uint64_t left,uint64_t right);
#endif
