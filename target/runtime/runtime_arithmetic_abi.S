/* ARM ABI glue, audited from reference disassembly. C owns arithmetic. */
.syntax unified
.cpu cortex-m0plus
.thumb
.macro FUNCTION name
.global \name
.type \name,%function
.thumb_func
\name:
.endm
FUNCTION syscon_rt_divzero
 bx lr
.size syscon_rt_divzero,.-syscon_rt_divzero

FUNCTION syscon_rt_uldivmod
 cmp r3,#0
 bne 1f
 cmp r2,#0
 bne 1f
 cmp r1,#0
 bne 2f
 cmp r0,#0
 beq 3f
2: movs r0,#0
 mvns r0,r0
 movs r1,r0
3: bx lr
1: push {r0,r1}
 mov r0,sp
 push {r0,lr}
 ldr r0,[sp,#8]
 bl syscon_rt_udiv64
 ldr r3,[sp,#4]
 mov lr,r3
 add sp,#8
 pop {r2,r3}
 bx lr
.size syscon_rt_uldivmod,.-syscon_rt_uldivmod

.macro FLAGCOMPARE name,impl
FUNCTION \name
 push {r0,r1,r2,r3,r4,lr}
 bl \impl
 cmp r0,#0
 bmi 1f
 movs r1,#0
 cmn r0,r1
1: pop {r0,r1,r2,r3,r4,pc}
.size \name,.-\name
.endm
FLAGCOMPARE syscon_rt_fcmp_flags,syscon_rt_fcmp_high
FLAGCOMPARE syscon_rt_dcmp_flags,syscon_rt_dcmp_high
FUNCTION syscon_rt_frcmp_flags
 mov r12,r0
 movs r0,r1
 mov r1,r12
 b syscon_rt_fcmp_flags
.size syscon_rt_frcmp_flags,.-syscon_rt_frcmp_flags
FUNCTION syscon_rt_drcmp_flags
 mov r12,r0
 movs r0,r2
 mov r2,r12
 mov r12,r1
 movs r1,r3
 mov r3,r12
 b syscon_rt_dcmp_flags
.size syscon_rt_drcmp_flags,.-syscon_rt_drcmp_flags

/* These helpers preserve R0/R1 and dispatch relative to LR's inline table. */
.macro BYTECASE name,load
FUNCTION \name
 push {r1}
 mov r1,lr
 lsrs r1,r1,#1
 lsls r1,r1,#1
 \load r1,[r1,r0]
 lsls r1,r1,#1
 add lr,r1
 pop {r1}
 bx lr
.size \name,.-\name
.endm
BYTECASE syscon_rt_case_sqi,ldrsb
BYTECASE syscon_rt_case_uqi,ldrb
FUNCTION syscon_rt_case_shi
 push {r0,r1}
 mov r1,lr
 lsrs r1,r1,#1
 lsls r0,r0,#1
 lsls r1,r1,#1
 ldrsh r1,[r1,r0]
 lsls r1,r1,#1
 add lr,r1
 pop {r0,r1}
 bx lr
.size syscon_rt_case_shi,.-syscon_rt_case_shi
.global __aeabi_uldivmod
.thumb_set __aeabi_uldivmod,syscon_rt_uldivmod
.global __aeabi_idiv0
.thumb_set __aeabi_idiv0,syscon_rt_divzero
.global __aeabi_ldiv0
.thumb_set __aeabi_ldiv0,syscon_rt_divzero
.global __aeabi_cfrcmple
.thumb_set __aeabi_cfrcmple,syscon_rt_frcmp_flags
.global __aeabi_cfcmpeq
.thumb_set __aeabi_cfcmpeq,syscon_rt_fcmp_flags
.global __aeabi_cfcmple
.thumb_set __aeabi_cfcmple,syscon_rt_fcmp_flags
.global __aeabi_cdrcmple
.thumb_set __aeabi_cdrcmple,syscon_rt_drcmp_flags
.global __aeabi_cdcmpeq
.thumb_set __aeabi_cdcmpeq,syscon_rt_dcmp_flags
.global __aeabi_cdcmple
.thumb_set __aeabi_cdcmple,syscon_rt_dcmp_flags
.global __gnu_thumb1_case_sqi
.thumb_set __gnu_thumb1_case_sqi,syscon_rt_case_sqi
.global __gnu_thumb1_case_uqi
.thumb_set __gnu_thumb1_case_uqi,syscon_rt_case_uqi
.global __gnu_thumb1_case_shi
.thumb_set __gnu_thumb1_case_shi,syscon_rt_case_shi
