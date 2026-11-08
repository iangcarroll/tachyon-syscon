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
    TEST_ADC_CHANNELS (rw) : ORIGIN = 0x200000f4, LENGTH = 72
    TEST_ADC_STATE (rw) : ORIGIN = 0x20000685, LENGTH = 11
    TEST_ADC_VREF (rw) : ORIGIN = 0x20000694, LENGTH = 1
    TEST_PWM (rw) : ORIGIN = 0x20000148, LENGTH = 36
    TEST_RGB (rw) : ORIGIN = 0x200003a8, LENGTH = 28
    TEST_GPIO_PINS (rw) : ORIGIN = 0x2000016c, LENGTH = 200
    TEST_GPIO_HANDLERS (rw) : ORIGIN = 0x20000698, LENGTH = 200
    TEST_RESET_CAUSE (rw) : ORIGIN = 0x20000254, LENGTH = 1
    TEST_I2C_BUS (rw) : ORIGIN = 0x2000013c, LENGTH = 12
    TEST_I2C_STATE (rw) : ORIGIN = 0x20000760, LENGTH = 2
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
    adc_channels PT_LOAD FLAGS(6);
    adc_state PT_LOAD FLAGS(6);
    adc_vref PT_LOAD FLAGS(6);
    pwm PT_LOAD FLAGS(6);
    rgb PT_LOAD FLAGS(6);
    gpio_pins PT_LOAD FLAGS(6);
    gpio_handlers PT_LOAD FLAGS(6);
    reset_cause PT_LOAD FLAGS(6);
    i2c_bus PT_LOAD FLAGS(6);
    i2c_state PT_LOAD FLAGS(6);
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
    .adc_channels : { *(.data.syscon_adc_channels) } > TEST_ADC_CHANNELS AT> TEST_CODE :adc_channels
    .adc_state (NOLOAD) : { *(.bss.syscon_adc_state) } > TEST_ADC_STATE :adc_state
    .adc_vref (NOLOAD) : { *(.bss.syscon_adc_vref_initialized) } > TEST_ADC_VREF :adc_vref
    .pwm : { *(.data.syscon_pwm_channels) } > TEST_PWM AT> TEST_CODE :pwm
    .rgb (NOLOAD) : { *(.bss.syscon_rgb_runtime) } > TEST_RGB :rgb
    .gpio_pins : { *(.data.syscon_gpio_pins) } > TEST_GPIO_PINS AT> TEST_CODE :gpio_pins
    .gpio_handlers (NOLOAD) : { *(.bss.syscon_gpio_handlers) } > TEST_GPIO_HANDLERS :gpio_handlers
    .reset_cause : { *(.data.syscon_reset_cause_cache) } > TEST_RESET_CAUSE AT> TEST_CODE :reset_cause
    .i2c_bus : { *(.data.syscon_i2c_bus) } > TEST_I2C_BUS AT> TEST_CODE :i2c_bus
    .i2c_state (NOLOAD) : { *(.bss.syscon_i2c_state) } > TEST_I2C_STATE :i2c_state
    .tasks (NOLOAD) : { *(.bss.syscon_task_state) } > TEST_TASKS :tasks
    .timers (NOLOAD) : { *(.bss.syscon_timer_state) } > TEST_TIMERS :timers
    .data : { *(.data*) } > TEST_DATA AT> TEST_CODE :data
    .bss (NOLOAD) : { *(.bss*) *(COMMON) } > TEST_DATA :data
    /DISCARD/ : { *(.comment) *(.note*) }
}
