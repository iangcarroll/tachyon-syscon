/* Physical-address exception experiment, NOT production linker/vector layout.
 * Only the standalone test modules/fixture reside in this upper-flash window. */
ENTRY(fixture_thread)
MEMORY { TEST_CODE (rx) : ORIGIN = 0xe800, LENGTH = 0x17f0 }
SECTIONS {
    .text : { *(.text*) *(.rodata*) } > TEST_CODE
    .ARM.exidx : { *(.ARM.exidx*) } > TEST_CODE
    /DISCARD/ : { *(.comment) *(.note*) }
}
