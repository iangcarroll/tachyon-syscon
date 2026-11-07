/* ARM frame adapters. Exposed bytes retain the original stack layout while
 * reconstructed C implements the logger and formatter algorithms. */
.syntax unified
.cpu cortex-m0plus
.thumb
.text
.global syscon_logger_target_vlog
.type syscon_logger_target_vlog,%function
.thumb_func
syscon_logger_target_vlog:
    mov r12,lr
    b .Lframe
.global syscon_logger_target_variadic_frame
.type syscon_logger_target_variadic_frame,%function
.thumb_func
syscon_logger_target_variadic_frame:
    push {r0}
    ldr r0,=0x8f97
    mov r12,r0
    pop {r0}
    b .Lframe
.global syscon_logger_target_mfg_frame
.type syscon_logger_target_mfg_frame,%function
.thumb_func
syscon_logger_target_mfg_frame:
    push {r0}
    ldr r0,=0x8fb3
    mov r12,r0
    pop {r0}
.Lframe:
    push {r4,r5,r6,r7,lr}
    sub sp,#348
    movs r4,r3
    movs r5,r0
    movs r6,r2
    movs r7,r1
    /* Preserve the actual relocated return separately below the exposed frame. */
    mov r0,sp
    sub sp,#16
    str r4,[sp]
    mov r1,lr
    str r1,[sp,#4]
    mov r1,r12
    str r1,[sp,#8]
    movs r2,#255
    adds r2,#109
    str r1,[r0,r2]
    ldr r3,=0x2000080c
    ldrb r3,[r3]
    cmp r3,#0
    beq .Ldisabled
    movs r1,r5
    movs r2,r7
    movs r3,r6
    bl syscon_logger_target_body
    mov r1,sp
    adds r1,#104
    movs r0,#0
    movs r2,#2
    bl syscon_target_uart_write
    b .Lcleanup
.Ldisabled:
    movs r0,r5
    movs r1,r7
    movs r2,r6
    movs r3,#0
.Lcleanup:
    push {r0,r1,r2,r3}
    /* An external write may corrupt the saved return. Preserve that behavior;
     * remap only the unchanged original return to this relocated wrapper. */
    mov r0,sp
    adds r0,#255
    adds r0,#141
    ldr r3,[r0]
    ldr r2,[sp,#24]
    cmp r3,r2
    bne 1f
    ldr r3,[sp,#20]
1:  mov r12,r3
    pop {r0,r1,r2,r3}
    add sp,#16
    add sp,#348
    pop {r4,r5,r6,r7}
    add sp,#4
    bx r12
.global syscon_logger_target
.type syscon_logger_target,%function
.thumb_func
syscon_logger_target:
    push {r2,r3}
    push {r0,r1,r2,lr}
    add r3,sp,#20
    str r3,[sp,#4]
    bl syscon_logger_target_variadic_frame
    add sp,#12
    pop {r3}
    add sp,#8
    bx r3
.global syscon_logger_target_mfg
.type syscon_logger_target_mfg,%function
.thumb_func
syscon_logger_target_mfg:
    push {r0,r1,r2,r3}
    push {r0,r1,r2,lr}
    movs r2,r0
    movs r0,#3
    ldr r1,=0xb849
    add r3,sp,#20
    str r3,[sp,#4]
    bl syscon_logger_target_mfg_frame
    add sp,#12
    pop {r3}
    add sp,#16
    bx r3
.global syscon_logger_target_snprintf
.type syscon_logger_target_snprintf,%function
.thumb_func
syscon_logger_target_snprintf:
    push {r2,r3}
    push {r0,r1,r2,lr}
    add r3,sp,#20
    str r3,[sp,#4]
    bl syscon_logger_target_vformat
    add sp,#12
    pop {r3}
    add sp,#8
    bx r3
.global syscon_logger_target_sg560d
.type syscon_logger_target_sg560d,%function
.thumb_func
syscon_logger_target_sg560d:
    push {r0,r1,r2,r3}
    push {r4,lr}
    sub sp,#136
    mov r0,sp
    ldr r1,[sp,#144]
    add r2,sp,#148
    bl syscon_logger_target_sg_body
    add sp,#136
    pop {r4}
    pop {r3}
    add sp,#16
    bx r3
.ltorg

/* Existing target-link names now resolve to the original-frame entries. */
.global syscon_target_logger
.thumb_set syscon_target_logger,syscon_logger_target
.global syscon_target_mfg_logger
.thumb_set syscon_target_mfg_logger,syscon_logger_target_mfg
.global syscon_target_sg560d_printf
.thumb_set syscon_target_sg560d_printf,syscon_logger_target_sg560d
.global syscon_target_snprintf
.thumb_set syscon_target_snprintf,syscon_logger_target_snprintf
