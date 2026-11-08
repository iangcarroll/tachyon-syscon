/* ARM variadic adapters. The legacy exposed buffers keep their layout, while
 * return addresses are ordinary linked call returns, never original literals. */
#include "logger_frame.h"
.syntax unified
.cpu cortex-m0plus
.thumb
.text
.global syscon_logger_target_vlog
.type syscon_logger_target_vlog,%function
.thumb_func
syscon_logger_target_vlog:
.global syscon_logger_target_variadic_frame
.type syscon_logger_target_variadic_frame,%function
.thumb_func
syscon_logger_target_variadic_frame:
.global syscon_logger_target_mfg_frame
.type syscon_logger_target_mfg_frame,%function
.thumb_func
syscon_logger_target_mfg_frame:
    push {r4,r5,r6,r7,lr}
    sub sp,#SYSCON_LOG_FRAME_SIZE
    movs r4,r3
    movs r5,r0
    movs r6,r2
    movs r7,r1
    /* Fifth C argument, with padding to preserve eight-byte call alignment. */
    mov r0,sp
    sub sp,#SYSCON_LOG_CALL_ARGS_SIZE
    str r4,[sp]
    ldr r3,=syscon_log_enabled
    ldrb r3,[r3]
    cmp r3,#0
    beq .Ldisabled
    movs r1,r5
    movs r2,r7
    movs r3,r6
    bl syscon_logger_target_body
    mov r1,sp
    adds r1,#SYSCON_LOG_SUFFIX_OFFSET
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
    /* Preserve UART R0-R3 results; return through the actual saved LR. */
    add sp,#SYSCON_LOG_CALL_ARGS_SIZE
    add sp,#SYSCON_LOG_FRAME_SIZE
    pop {r4,r5,r6,r7,pc}
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
    ldr r1,=syscon_log_mfg_tag
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
    sub sp,#SYSCON_SG_FRAME_SIZE
    mov r0,sp
    ldr r1,[sp,#(SYSCON_SG_FRAME_SIZE+8)]
    add r2,sp,#(SYSCON_SG_FRAME_SIZE+12)
    bl syscon_logger_target_sg_body
    add sp,#SYSCON_SG_FRAME_SIZE
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
