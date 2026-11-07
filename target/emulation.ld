/* Deliberately relocated test image. This is not a device flash layout. */
ENTRY(syscon_rgb_scale)
MEMORY {
    TEST_CODE (rx) : ORIGIN = 0x01000000, LENGTH = 512K
    TEST_DATA (rw) : ORIGIN = 0x21000000, LENGTH = 32K
    /* Per-function fixtures intentionally share the oracle's cache location.
       The physical linker has no such placement constraint. */
    TEST_CONFIG (rw) : ORIGIN = 0x20000030, LENGTH = 22
    TEST_KEY_RANGES (rw) : ORIGIN = 0x200000b4, LENGTH = 36
    TEST_KEY_CONTROL (rw) : ORIGIN = 0x200000d8, LENGTH = 2
    TEST_KEY_RUNTIME (rw) : ORIGIN = 0x20000390, LENGTH = 24
    TEST_RETAINED (rw) : ORIGIN = 0x200000da, LENGTH = 3
    TEST_TASKS (rw) : ORIGIN = 0x20000534, LENGTH = 216
    TEST_TIMERS (rw) : ORIGIN = 0x20000610, LENGTH = 112
}
PHDRS {
    code PT_LOAD FLAGS(5);
    config PT_LOAD FLAGS(6);
    key_ranges PT_LOAD FLAGS(6);
    key_control PT_LOAD FLAGS(6);
    key_runtime PT_LOAD FLAGS(6);
    retained PT_LOAD FLAGS(6);
    tasks PT_LOAD FLAGS(6);
    timers PT_LOAD FLAGS(6);
    data PT_LOAD FLAGS(6);
}
SECTIONS {
    .text : {
        *(.text*)
        *(.rodata*)
    } > TEST_CODE :code
    .ARM.exidx : { *(.ARM.exidx*) } > TEST_CODE :code
    .config_state : { *(.data.syscon_config_state) } > TEST_CONFIG AT> TEST_CODE :config
    .key_ranges : { *(.data.syscon_powerkey_ranges) } > TEST_KEY_RANGES AT> TEST_CODE :key_ranges
    .key_control : { *(.data.syscon_powerkey_control) } > TEST_KEY_CONTROL AT> TEST_CODE :key_control
    .key_runtime (NOLOAD) : { *(.bss.syscon_powerkey_runtime) } > TEST_KEY_RUNTIME :key_runtime
    .retained (NOLOAD) : { *(.bss.syscon_retained_state) } > TEST_RETAINED :retained
    .tasks (NOLOAD) : { *(.bss.syscon_task_state) } > TEST_TASKS :tasks
    .timers (NOLOAD) : { *(.bss.syscon_timer_state) } > TEST_TIMERS :timers
    .data : { *(.data*) } > TEST_DATA AT> TEST_CODE :data
    .bss (NOLOAD) : { *(.bss*) *(COMMON) } > TEST_DATA :data
    /DISCARD/ : { *(.comment) *(.note*) }
}
