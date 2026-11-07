/* Deliberately relocated test image. This is not a device flash layout. */
ENTRY(syscon_rgb_scale)
MEMORY {
    TEST_CODE (rx) : ORIGIN = 0x01000000, LENGTH = 512K
    TEST_DATA (rw) : ORIGIN = 0x21000000, LENGTH = 32K
}
SECTIONS {
    .text : {
        *(.text*)
        *(.rodata*)
    } > TEST_CODE
    .ARM.exidx : { *(.ARM.exidx*) } > TEST_CODE
    .data : { *(.data*) } > TEST_DATA AT> TEST_CODE
    .bss (NOLOAD) : { *(.bss*) *(COMMON) } > TEST_DATA
    /DISCARD/ : { *(.comment) *(.note*) }
}
