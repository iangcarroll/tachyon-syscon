/* Target soft-float adapters: preserve original unsigned conversion policy. */
#include "runtime_arithmetic.h"
int syscon_rt_f_ge(uint32_t,uint32_t);
int syscon_rt_d_ge(uint64_t,uint64_t);
extern float __aeabi_fsub(float,float);
extern double __aeabi_dsub(double,double);
extern int __aeabi_f2iz(float);
extern int __aeabi_d2iz(double);
uint32_t syscon_rt_f2u(uint32_t a) {
    union {uint32_t u;float f;} x={a},limit={0x4f000000};
    if(syscon_rt_f_ge(a,limit.u))return (uint32_t)__aeabi_f2iz(__aeabi_fsub(x.f,limit.f))+0x80000000u;
    return (uint32_t)__aeabi_f2iz(x.f);
}
uint32_t syscon_rt_d2u(uint64_t a) {
    union {uint64_t u;double d;} x={a},limit={UINT64_C(0x41e0000000000000)};
    if(syscon_rt_d_ge(a,limit.u))return (uint32_t)__aeabi_d2iz(__aeabi_dsub(x.d,limit.d))+0x80000000u;
    return (uint32_t)__aeabi_d2iz(x.d);
}
extern __typeof(syscon_rt_f2u) __aeabi_f2uiz __attribute__((alias("syscon_rt_f2u")));
extern __typeof(syscon_rt_d2u) __aeabi_d2uiz __attribute__((alias("syscon_rt_d2u")));
