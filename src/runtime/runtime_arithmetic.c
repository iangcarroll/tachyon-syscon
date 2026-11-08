/* SPDX-License-Identifier: GPL-3.0-or-later WITH GCC-exception-3.1
 * The udiv64 align/subtract algorithm is adapted from GCC 13.3 libgcc2.c,
 * Copyright (C) 1989-2023 Free Software Foundation, Inc.
 * See vendor/gcc-soft-fp/COPYING3 and COPYING.RUNTIME. Other helpers were
 * reconstructed from the pinned firmware disassembly in this project. */
/* Integer and comparison semantics audited against syscon-1.0.52 ARM code.
 * No signed overflow, undefined shifts, native FP or installed runtime calls. */
#include "runtime_arithmetic.h"

uint32_t syscon_rt_clz32(uint32_t x) {
    uint32_t n=32;
    while(x){--n;x>>=1;}
    return n;
}
uint32_t __clzsi2(uint32_t x){return syscon_rt_clz32(x);}
uint32_t syscon_rt_clz64(uint64_t x) {
    uint32_t hi=(uint32_t)(x>>32);
    return hi?syscon_rt_clz32(hi):32+syscon_rt_clz32((uint32_t)x);
}
uint64_t syscon_rt_udiv32(uint32_t n,uint32_t d) {
    uint32_t q=0,r=0;
    if(!d)return (uint64_t)n<<32;
    for(unsigned i=32;i;--i){
        uint32_t carry=r>>31;r=(r<<1)|((n>>(i-1))&1);
        if(carry||r>=d){r-=d;q|=UINT32_C(1)<<(i-1);}
    }
    return ((uint64_t)r<<32)|q;
}
uint64_t syscon_rt_idiv32(uint32_t n,uint32_t d) {
    if(!d)return (uint64_t)n<<32;
    uint32_t negn=n>>31,negd=d>>31;
    uint64_t qr=syscon_rt_udiv32(negn?0u-n:n,negd?0u-d:d);
    uint32_t q=(uint32_t)qr,r=(uint32_t)(qr>>32);
    if(negn^negd)q=0u-q;
    if(negn)r=0u-r;
    return ((uint64_t)r<<32)|q;
}
uint64_t syscon_rt_mul64(uint64_t x,uint64_t y) {
    uint32_t a=(uint32_t)x,b=(uint32_t)y;
    uint32_t a0=a&65535,a1=a>>16,b0=b&65535,b1=b>>16;
    uint32_t lo=a0*b0,mid=a1*b0,high=a1*b1;
    uint32_t sum=(lo>>16)+a0*b1+mid;
    if(sum<mid)high+=65536;
    high+=(sum>>16)+(uint32_t)(x>>32)*b+a*(uint32_t)(y>>32);
    return ((uint64_t)high<<32)|((sum<<16)|(lo&65535));
}
/* Explicit full-width shifts preserve the original ARM logical-shift result
 * when this internal routine is called with divisor zero (outside C / domain). */
static uint64_t lshift(uint64_t x,unsigned n){return n>=64?0:x<<n;}
static uint64_t rshift(uint64_t x,unsigned n){return n>=64?0:x>>n;}
uint64_t syscon_rt_udiv64(uint64_t n,uint64_t d,uint64_t *rem) {
    uint64_t q=0,r=n;
    if(d<=r){
        unsigned k=syscon_rt_clz64(d)-syscon_rt_clz64(n);
        uint64_t y=lshift(d,k);
        if(r>=y){r-=y;q=lshift(1,k);}
        if(k){
            y>>=1;
            for(unsigned i=k;i;--i)r=r>=y?((r-y)<<1)+1:r<<1;
            q+=r;r=rshift(r,k);q-=lshift(r,k);
        }
    }
    if(rem)*rem=r;
    return q;
}
static int cmp32(uint32_t a,uint32_t b,int unordered) {
    uint32_t am=a&0x7fffffff,bm=b&0x7fffffff;
    if(am>0x7f800000||bm>0x7f800000)return unordered;
    if((!am&&!bm)||a==b)return 0;
    if((a^b)>>31)return a>>31?-1:1;
    return (am<bm)^(a>>31)?-1:1;
}
static int cmp64(uint64_t a,uint64_t b,int unordered) {
    uint64_t am=a&UINT64_C(0x7fffffffffffffff),bm=b&UINT64_C(0x7fffffffffffffff);
    if(am>UINT64_C(0x7ff0000000000000)||bm>UINT64_C(0x7ff0000000000000))return unordered;
    if((!am&&!bm)||a==b)return 0;
    if((a^b)>>63)return a>>63?-1:1;
    return (am<bm)^(unsigned)(a>>63)?-1:1;
}
int syscon_rt_fcmp_low(uint32_t a,uint32_t b){return cmp32(a,b,-2);}
int syscon_rt_fcmp_high(uint32_t a,uint32_t b){return cmp32(a,b,2);}
int syscon_rt_fne(uint32_t a,uint32_t b){return cmp32(a,b,2)!=0;}
int syscon_rt_dcmp_low(uint64_t a,uint64_t b){return cmp64(a,b,-2);}
int syscon_rt_dcmp_high(uint64_t a,uint64_t b){return cmp64(a,b,2);}
int syscon_rt_dne(uint64_t a,uint64_t b){return cmp64(a,b,2)!=0;}
#define COMPARE_WRAPPERS(prefix,type,cmp) \
 int prefix##_eq(type a,type b){return cmp(a,b,2)==0;} \
 int prefix##_lt(type a,type b){return cmp(a,b,2)<0;} \
 int prefix##_le(type a,type b){return cmp(a,b,2)<=0;} \
 int prefix##_gt(type a,type b){return cmp(a,b,-2)>0;} \
 int prefix##_ge(type a,type b){return cmp(a,b,-2)>=0;}
COMPARE_WRAPPERS(syscon_rt_f,uint32_t,cmp32)
COMPARE_WRAPPERS(syscon_rt_d,uint64_t,cmp64)
uint64_t syscon_rt_udivmod32(uint32_t n,uint32_t d){return syscon_rt_udiv32(n,d);}
uint64_t syscon_rt_idivmod32(uint32_t n,uint32_t d){return syscon_rt_idiv32(n,d);}

#if defined(__arm__) && !defined(__ARM_PCS_VFP)
/* Target aliases use the verified soft-float register ABI. Division's C uint64
 * return intentionally carries the remainder in R1 even for quotient callers. */
#define TARGET_ALIAS(name,implementation) \
 extern __typeof(implementation) name __attribute__((alias(#implementation)));
TARGET_ALIAS(__aeabi_uidiv,syscon_rt_udiv32)
TARGET_ALIAS(__aeabi_uidivmod,syscon_rt_udivmod32)
TARGET_ALIAS(__aeabi_idiv,syscon_rt_idiv32)
TARGET_ALIAS(__aeabi_idivmod,syscon_rt_idivmod32)
TARGET_ALIAS(__aeabi_lmul,syscon_rt_mul64)
TARGET_ALIAS(__clzdi2,syscon_rt_clz64)
TARGET_ALIAS(__aeabi_fcmpeq,syscon_rt_f_eq)
TARGET_ALIAS(__aeabi_fcmplt,syscon_rt_f_lt)
TARGET_ALIAS(__aeabi_fcmple,syscon_rt_f_le)
TARGET_ALIAS(__aeabi_fcmpgt,syscon_rt_f_gt)
TARGET_ALIAS(__aeabi_fcmpge,syscon_rt_f_ge)
TARGET_ALIAS(__aeabi_dcmpeq,syscon_rt_d_eq)
TARGET_ALIAS(__aeabi_dcmplt,syscon_rt_d_lt)
TARGET_ALIAS(__aeabi_dcmple,syscon_rt_d_le)
TARGET_ALIAS(__aeabi_dcmpgt,syscon_rt_d_gt)
TARGET_ALIAS(__aeabi_dcmpge,syscon_rt_d_ge)
#undef TARGET_ALIAS
#endif
