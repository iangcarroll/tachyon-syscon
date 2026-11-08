/* Deliberately relocated test image. This is not a device flash layout. */
ENTRY(syscon_rgb_scale)
MEMORY {
    TEST_CODE (rx) : ORIGIN = 0x01000000, LENGTH = 512K
    TEST_DATA (rw) : ORIGIN = 0x21000000, LENGTH = 32K
    /* Per-function fixtures intentionally share the oracle's cache location.
       The physical linker has no such placement constraint. */
    TEST_DIAGNOSTICS_FLAG (rw) : ORIGIN = 0x20000046, LENGTH = 1
    TEST_DIAGNOSTICS_STATE (rw) : ORIGIN = 0x200002c0, LENGTH = 16
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
    TEST_UART_PORTS (rw) : ORIGIN = 0x20000234, LENGTH = 32
    TEST_UART_CONFIG (rw) : ORIGIN = 0x20000762, LENGTH = 18
    TEST_UART_RINGS (rw) : ORIGIN = 0x20000774, LENGTH = 152
    TEST_POWER_MINIMUM (rw) : ORIGIN = 0x2000005c, LENGTH = 4
    TEST_POWER_NAMES (rw) : ORIGIN = 0x20000060, LENGTH = 84
    TEST_SHUTDOWN_REASON (rw) : ORIGIN = 0x2000036f, LENGTH = 1
    TEST_USB_REATTACH (rw) : ORIGIN = 0x20000370, LENGTH = 16
    TEST_SHUTDOWN (rw) : ORIGIN = 0x20000380, LENGTH = 16
    TEST_PROTOCOL_DEBUG (rw) : ORIGIN = 0x200002ee, LENGTH = 1
    TEST_CONSOLE_PARSER (rw) : ORIGIN = 0x20000048, LENGTH = 20
    TEST_CONSOLE_BUFFER (rw) : ORIGIN = 0x200002ef, LENGTH = 128
    TEST_KEY_EVENTS (rw) : ORIGIN = 0x200002d8, LENGTH = 20
    TEST_KEY_EVENT_BUFFER (rw) : ORIGIN = 0x200002d1, LENGTH = 4
    TEST_SHUTDOWN_PENDING (rw) : ORIGIN = 0x200002ec, LENGTH = 1
    TEST_KEY_STARTED_OFF (rw) : ORIGIN = 0x200002ed, LENGTH = 1
    TEST_WAKEUP_PENDING (rw) : ORIGIN = 0x20000680, LENGTH = 1
    TEST_IOEXPANDER_INITIALIZED (rw) : ORIGIN = 0x200002d0, LENGTH = 1
    TEST_RUNTIME_CURRENT (rw) : ORIGIN = 0x20000258, LENGTH = 4
    TEST_RUNTIME_CONTEXT (rw) : ORIGIN = 0x2000025c, LENGTH = 100
    TEST_RUNTIME_HEAP (rw) : ORIGIN = 0x20000810, LENGTH = 16
    TEST_MODEM_PARSER (rw) : ORIGIN = 0x200000e0, LENGTH = 20
    TEST_MODEM_BOOT (rw) : ORIGIN = 0x200003c4, LENGTH = 12
    TEST_MODEM_SCRATCH (rw) : ORIGIN = 0x200003d0, LENGTH = 128
    TEST_MODEM_TIMING (rw) : ORIGIN = 0x20000450, LENGTH = 16
    TEST_MODEM_BUFFER (rw) : ORIGIN = 0x20000460, LENGTH = 128
    TEST_MODEM_RUNTIME (rw) : ORIGIN = 0x200004e0, LENGTH = 84
    TEST_LOG (rw) : ORIGIN = 0x2000080c, LENGTH = 1
    TEST_TASKS (rw) : ORIGIN = 0x20000534, LENGTH = 216
    TEST_TIMERS (rw) : ORIGIN = 0x20000610, LENGTH = 112
}
PHDRS {
    code PT_LOAD FLAGS(5);
    config PT_LOAD FLAGS(6);
    diagnostics_flag PT_LOAD FLAGS(6);
    diagnostics_state PT_LOAD FLAGS(6);
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
    uart_ports PT_LOAD FLAGS(6);
    uart_config PT_LOAD FLAGS(6);
    uart_rings PT_LOAD FLAGS(6);
    power_minimum PT_LOAD FLAGS(6);
    power_names PT_LOAD FLAGS(6);
    shutdown_reason PT_LOAD FLAGS(6);
    usb_reattach PT_LOAD FLAGS(6);
    shutdown PT_LOAD FLAGS(6);
    protocol_debug PT_LOAD FLAGS(6);
    console_parser PT_LOAD FLAGS(6);
    console_buffer PT_LOAD FLAGS(6);
    key_events PT_LOAD FLAGS(6);
    key_event_buffer PT_LOAD FLAGS(6);
    shutdown_pending PT_LOAD FLAGS(6);
    key_started_off PT_LOAD FLAGS(6);
    wakeup_pending PT_LOAD FLAGS(6);
    ioexpander_initialized PT_LOAD FLAGS(6);
    runtime_current PT_LOAD FLAGS(6);
    runtime_context PT_LOAD FLAGS(6);
    runtime_heap PT_LOAD FLAGS(6);
    modem_parser PT_LOAD FLAGS(6);
    modem_boot PT_LOAD FLAGS(6);
    modem_scratch PT_LOAD FLAGS(6);
    modem_timing PT_LOAD FLAGS(6);
    modem_buffer PT_LOAD FLAGS(6);
    modem_runtime PT_LOAD FLAGS(6);
    log PT_LOAD FLAGS(6);
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
    .diagnostics_flag : { *(.data.syscon_diagnostics_enabled) } > TEST_DIAGNOSTICS_FLAG AT> TEST_CODE :diagnostics_flag
    .diagnostics_state (NOLOAD) : { *(.bss.syscon_diagnostics_state) } > TEST_DIAGNOSTICS_STATE :diagnostics_state
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
    .uart_ports : { *(.data.syscon_uart_ports) } > TEST_UART_PORTS AT> TEST_CODE :uart_ports
    .uart_config (NOLOAD) : { *(.bss.syscon_uart_config) } > TEST_UART_CONFIG :uart_config
    .uart_rings (NOLOAD) : { *(.bss.syscon_uart_rings) } > TEST_UART_RINGS :uart_rings
    .power_minimum : { *(.data.syscon_minimum_vph_mv) } > TEST_POWER_MINIMUM AT> TEST_CODE :power_minimum
    .power_names : { *(.data.syscon_power_names) } > TEST_POWER_NAMES AT> TEST_CODE :power_names
    .shutdown_reason (NOLOAD) : { *(.bss.syscon_shutdown_reason) } > TEST_SHUTDOWN_REASON :shutdown_reason
    .usb_reattach (NOLOAD) : { *(.bss.syscon_usb_reattach_state) } > TEST_USB_REATTACH :usb_reattach
    .shutdown (NOLOAD) : { *(.bss.syscon_shutdown_state) } > TEST_SHUTDOWN :shutdown
    .protocol_debug (NOLOAD) : { *(.bss.syscon_protocol_debug) } > TEST_PROTOCOL_DEBUG :protocol_debug
    .console_parser : { *(.data.syscon_console_parser) } > TEST_CONSOLE_PARSER AT> TEST_CODE :console_parser
    .console_buffer (NOLOAD) : { *(.bss.syscon_console_buffer) } > TEST_CONSOLE_BUFFER :console_buffer
    .key_events (NOLOAD) : { *(.bss.syscon_key_events) } > TEST_KEY_EVENTS :key_events
    .key_event_buffer (NOLOAD) : { *(.bss.syscon_key_event_buffer) } > TEST_KEY_EVENT_BUFFER :key_event_buffer
    .shutdown_pending (NOLOAD) : { *(.bss.syscon_shutdown_pending) } > TEST_SHUTDOWN_PENDING :shutdown_pending
    .key_started_off (NOLOAD) : { *(.bss.syscon_key_started_off) } > TEST_KEY_STARTED_OFF :key_started_off
    .wakeup_pending (NOLOAD) : { *(.bss.syscon_wakeup_pending) } > TEST_WAKEUP_PENDING :wakeup_pending
    .ioexpander_initialized (NOLOAD) : { *(.bss.syscon_ioexpander_initialized) } > TEST_IOEXPANDER_INITIALIZED :ioexpander_initialized
    .runtime_current : { *(.data.syscon_runtime_current) } > TEST_RUNTIME_CURRENT AT> TEST_CODE :runtime_current
    .runtime_context : { *(.data.syscon_runtime_context) } > TEST_RUNTIME_CONTEXT AT> TEST_CODE :runtime_context
    .runtime_heap (NOLOAD) : { *(.bss.syscon_runtime_heap) } > TEST_RUNTIME_HEAP :runtime_heap
    .modem_parser : { *(.data.syscon_modem_parser) } > TEST_MODEM_PARSER AT> TEST_CODE :modem_parser
    .modem_boot (NOLOAD) : { *(.bss.syscon_modem_boot) } > TEST_MODEM_BOOT :modem_boot
    .modem_scratch (NOLOAD) : { *(.bss.syscon_modem_scratch) } > TEST_MODEM_SCRATCH :modem_scratch
    .modem_timing (NOLOAD) : { *(.bss.syscon_modem_timing) } > TEST_MODEM_TIMING :modem_timing
    .modem_buffer (NOLOAD) : { *(.bss.syscon_modem_buffer) } > TEST_MODEM_BUFFER :modem_buffer
    .modem_runtime (NOLOAD) : { *(.bss.syscon_modem_runtime) } > TEST_MODEM_RUNTIME :modem_runtime
    .log (NOLOAD) : { *(.bss.syscon_log_enabled) } > TEST_LOG :log
    .tasks (NOLOAD) : { *(.bss.syscon_task_state) } > TEST_TASKS :tasks
    .timers (NOLOAD) : { *(.bss.syscon_timer_state) } > TEST_TIMERS :timers
    .data : { *(.data*) } > TEST_DATA AT> TEST_CODE :data
    .bss (NOLOAD) : { *(.bss*) *(COMMON) } > TEST_DATA :data
    /DISCARD/ : { *(.comment) *(.note*) }
}
