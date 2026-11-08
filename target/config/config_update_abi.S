/* Capture the caller SP before any compiled C prologue for the original
 * compaction diagnostic. Original total frame was20+564=584bytes. */
.syntax unified
.cpu cortex-m0plus
.thumb
.text
.global syscon_cfg_compact
.type syscon_cfg_compact,%function
.thumb_func
syscon_cfg_compact:
    mov r3,sp
    subs r3,#255
    subs r3,#255
    subs r3,#74
    /* ARMv6-M short B cannot span a complete linked image. Tail transfer
     * through a literal keeps the original incoming SP and all four args. */
    mov ip,r4
    ldr r4,=syscon_cfg_compact_body
    push {r4}
    mov r4,ip
    pop {pc}

.global syscon_cfg_runtime_update
.type syscon_cfg_runtime_update,%function
.thumb_func
syscon_cfg_runtime_update:
    mov r2,sp
    subs r2,#80
    ldr r3,=syscon_cfg_runtime_update_body
    bx r3
.ltorg
