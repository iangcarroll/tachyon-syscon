/* ARM32 ABI glue for the original nano formatter's stack-dependent state.
 * All parsing/conversion remains reconstructed C. */
.syntax unified
.cpu cortex-m0plus
.thumb
.section .text.syscon_rt_vfprintf,"ax",%progbits
.global syscon_rt_vfprintf
.type syscon_rt_vfprintf,%function
.thumb_func
syscon_rt_vfprintf:
    /* Original0x9b24's uninitialized n lives at incomingSP-136. Capture it
     * before the rebuilt C prologue can overwrite that location. */
    push {r4,lr}
    mov r4,sp
    subs r4,#128
    ldr r4,[r4]
    sub sp,#8
    str r4,[sp]
    /* Alternate octal also reads initial print_state.size at incomingSP-104. */
    mov r4,sp
    subs r4,#88
    ldr r4,[r4]
    str r4,[sp,#4]
    bl syscon_rt_vfprintf_seeded
    add sp,#8
    pop {r4,pc}
.size syscon_rt_vfprintf,.-syscon_rt_vfprintf

.section .text.syscon_rt_snprintf,"ax",%progbits
.global syscon_rt_snprintf
.type syscon_rt_snprintf,%function
.thumb_func
syscon_rt_snprintf:
    /* Preserve original0x976c's 136-byte frame and saved argument placement.
     * This makes its child's uninitialized n reside at callerSP-272 too. */
    push {r2,r3}
    push {r4,r5,lr}
    ldr r3,=0x20000258
    movs r4,r1
    ldr r5,[r3]
    sub sp,#116
    cmp r1,#0
    bge 1f
    movs r3,#139
    movs r0,#1
    str r3,[r5]
    rsbs r0,r0,#0
    b 4f
1:
    movs r3,#130
    mov r2,sp
    lsls r3,r3,#2
    strh r3,[r2,#20]
    movs r3,#0
    str r0,[sp,#8]
    str r0,[sp,#24]
    cmp r1,r3
    beq 2f
    subs r3,r1,#1
2:
    str r3,[sp,#16]
    str r3,[sp,#28]
    movs r3,#1
    mov r2,sp
    rsbs r3,r3,#0
    strh r3,[r2,#22]
    movs r0,r5
    add r3,sp,#132
    ldr r2,[sp,#128]
    add r1,sp,#8
    str r3,[sp,#4]
    bl syscon_rt_vfprintf
    adds r3,r0,#1
    bge 3f
    movs r3,#139
    str r3,[r5]
3:
    cmp r4,#0
    beq 4f
    movs r3,#0
    ldr r2,[sp,#8]
    strb r3,[r2]
4:
    add sp,#116
    pop {r4,r5}
    pop {r3}
    add sp,#8
    bx r3
.size syscon_rt_snprintf,.-syscon_rt_snprintf
.ltorg
