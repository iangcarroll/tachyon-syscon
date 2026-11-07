/* Original8c8c frame and caller-saved return-register effects. */
.syntax unified
.cpu cortex-m0plus
.thumb
.text
.global syscon_target_uart_write_buffer
.type syscon_target_uart_write_buffer,%function
.thumb_func
syscon_target_uart_write_buffer:
    push {r0,r1,r2,r4,r5,r6,r7,lr}
    str r2,[sp,#4]
    bl syscon_target_uart_write_buffer_body
    movs r0,#0
    pop {r1,r2,r3,r4,r5,r6,r7,pc}
.size syscon_target_uart_write_buffer,.-syscon_target_uart_write_buffer
