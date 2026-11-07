/* Physical-address exception experiment, NOT production linker/vector layout.
 * Only the standalone test modules/fixture reside in this upper-flash window. */
ENTRY(fixture_thread)
MEMORY {
    TEST_CODE (rx) : ORIGIN = 0xe800, LENGTH = 0x17f0
    TEST_RETAINED (rw) : ORIGIN = 0x200000da, LENGTH = 3
    TEST_TASKS (rw) : ORIGIN = 0x20000534, LENGTH = 216
    TEST_TIMERS (rw) : ORIGIN = 0x20000610, LENGTH = 112
}
SECTIONS {
    .text : { *(.text*) *(.rodata*) } > TEST_CODE
    .ARM.exidx : { *(.ARM.exidx*) } > TEST_CODE
    .retained (NOLOAD) : { *(.bss.syscon_retained_state) } > TEST_RETAINED
    .tasks (NOLOAD) : { *(.bss.syscon_task_state) } > TEST_TASKS
    .timers (NOLOAD) : { *(.bss.syscon_timer_state) } > TEST_TIMERS
    /DISCARD/ : { *(.comment) *(.note*) }
}
