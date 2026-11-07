/* ABI glue for the original write_slot's exposed 64-byte local buffer.
 * Validation, storage and all formatting remain reconstructed C.
 * Missing variadic arguments read the live original-shaped slot frame. */
.syntax unified
.cpu cortex-m0plus
.thumb
.section .text.syscon_cfg_write_slot,"ax",%progbits
.global syscon_cfg_write_slot
.type syscon_cfg_write_slot,%function
.thumb_func
syscon_cfg_write_slot:
    push {r4,r5,r6,lr}
    sub sp,#64
    mov r4,r0
    mov r6,r1
    mov r5,r2
    bl syscon_cfg_prepare_slot
    cmp r0,#0
    beq 1f
    mov r0,sp
    movs r1,#0
    movs r2,#64
    bl syscon_rt_memset
    mov r0,sp
    movs r1,#255
    movs r2,#64
    bl syscon_rt_memset
    /* Original memset leaves one-past-buffer in R3. This is the first
     * absent argument; actual following arguments alias the live buffer. */
    mov r0,sp
    movs r1,#31
    mov r2,r6
    add r3,sp,#64
    bl syscon_rt_snprintf
    add r0,sp,#32
    movs r1,#31
    mov r2,r5
    /* Original snprintf returns with its saved return address in R3.
     * Its numeric value is consumed by legacy format-bearing flash values. */
    ldr r3,=0x2919
    bl syscon_rt_snprintf
    mov r0,r4
    mov r1,sp
    bl syscon_cfg_finish_slot
1:
    add sp,#64
    pop {r4,r5,r6,pc}
.size syscon_cfg_write_slot,.-syscon_cfg_write_slot
.ltorg
