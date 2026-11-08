/* Physical geometry of the unconfirmed MSPM0L1306 profile; not flash approval. */
ENTRY(syscon_physical_reset)
MEMORY {
 CODE (rx) : ORIGIN = 0x00000000, LENGTH = 0xf7f8
 VERSION_REGION (r) : ORIGIN = 0xf7f8, LENGTH = 8
 IDENTITY (r) : ORIGIN = 0xf800, LENGTH = 0x400
 CONFIG (r) : ORIGIN = 0xfc00, LENGTH = 0x400
 SRAM (rwx) : ORIGIN = 0x20000000, LENGTH = 0x1000
}
__stack_top = ORIGIN(SRAM) + LENGTH(SRAM);
/* Separate PT_LOAD flags distinguish code and read-only data in the ELF.
   The MCU does not acquire memory protection from ELF program headers. */
PHDRS {
 vectors PT_LOAD FLAGS(4);
 ram_exec PT_LOAD FLAGS(5);
 ram_extra PT_LOAD FLAGS(7);
 early PT_LOAD FLAGS(5);
 text PT_LOAD FLAGS(5);
 config_data PT_LOAD FLAGS(4);
 peripheral_rodata PT_LOAD FLAGS(4);
 application_rodata PT_LOAD FLAGS(4);
 version PT_LOAD FLAGS(4);
 state PT_LOAD FLAGS(6);
 auxiliary PT_LOAD FLAGS(6);
 initialized PT_LOAD FLAGS(6);
 peripherals PT_LOAD FLAGS(6);
 peripheral_bss PT_LOAD FLAGS(6);
 irq_state PT_LOAD FLAGS(6);
 power_data PT_LOAD FLAGS(6);
 power_state PT_LOAD FLAGS(6);
 protocol_data PT_LOAD FLAGS(6);
 application_state PT_LOAD FLAGS(6);
 modem_state PT_LOAD FLAGS(6);
 runtime_data PT_LOAD FLAGS(6);
}
SECTIONS {
 .vectors : {KEEP(*(.vectors))} > CODE :vectors
 .ram_exec : {
   __ram_exec_start = .; KEEP(*(.ram_original_flash))
   __ram_exec_used_end = .; .  =  __ram_exec_start+0x30; __ram_exec_end = .;
 } > SRAM AT> CODE :ram_exec
 __ram_exec_load = LOADADDR(.ram_exec);
 .ram_extra : {
   __ram_extra_start = .;
   /* Additional RAM sections require explicit review; direct flash needs none. */
   .  =  ALIGN(4);__ram_extra_end = .;
 } > SRAM AT> CODE :ram_extra
 __ram_extra_load = LOADADDR(.ram_extra);
 .command_table : {KEEP(*(.rodata.syscon_target_commands))} > CODE :application_rodata
 .version : {KEEP(*(.firmware_version))} > VERSION_REGION :version
 .text_early : {
   *src_runtime_callback_helpers.o(.text*)
   *src_config_config_helpers.o(.text*)
   *src_config_config_read.o(.text*)
   *src_config_config_storage.o(.text*)
   *src_drivers_core_helpers.o(.text*)
   *src_runtime_interface_bindings.o(.text*)
   *src_drivers_fault_control_target.o(.text*)
   *src_drivers_fault_handlers.o(.text*)
   *src_drivers_hal_helpers.o(.text*)
   *src_drivers_mspm0_core_target.o(.text*)
   *src_drivers_uart_ring.o(.text*)
   *src_runtime_runtime_arithmetic_abi.o(.text*)
   *src_runtime_runtime_heap.o(.text*)
   *src_runtime_runtime_scan.o(.text*)
   *src_runtime_runtime_scan_abi.o(.text*)
   *src_runtime_runtime_scan_printf.o(.text*)
   *src_runtime_runtime_scan_wrappers.o(.text*)
   *src_runtime_runtime_stdio.o(.text*)
   *src_runtime_runtime_support.o(.text*)
   *src_runtime_runtime_arithmetic_float.o(.text*)
 } > CODE :early
 /* All private objects are linker allocated; no recovered image placements. */
 .config_data : { *src_config*.o(.rodata*) } > CODE :config_data
 .peripheral_rodata : {
   *src_drivers_mspm0_core_target.o(.rodata*)
   *src_drivers_fault_control_target.o(.rodata*)
   *src_drivers_i2c_target.o(.rodata*)
   *src_drivers_uart_hal_target.o(.rodata*) *src_drivers_uart_ring.o(.rodata*)
   *src_power_power_manager_target.o(.rodata*) *src_power_power_policy_target.o(.rodata*)
   *src_power_power_state.o(.rodata*)
 } > CODE :peripheral_rodata
 .application_rodata : {
   *src_drivers_core_helpers.o(.rodata*) *src_drivers_flash_abi_target.o(.rodata*)
   *src_drivers_ioexpander_target.o(.rodata*)
   *src_power_retained_target.o(.rodata*) *src_scheduling_tasks_target.o(.rodata*) *src_scheduling_timers_target.o(.rodata*)
   *src_runtime_runtime_state.o(.rodata*)
   *src_modem_modem_state.o(.rodata*)
   *src_app_diagnostics_target.o(.rodata*)
   *src_modem_sg560d_target.o(.rodata*)
   *src_app_application_target.o(.rodata*)
   *src_protocol_command_table_target.o(.rodata*)
   *src_protocol_protocol_target.o(.rodata*)
   *src_protocol_control_commands_target.o(.rodata*)
 } > CODE :application_rodata
 .text : { *(.text*) *(.rodata*) } > CODE :text
 .ARM.exidx : {* (.ARM.exidx*)} > CODE :text
 .peripheral_data : ALIGN(4) {
   __peripheral_data_start = .; *(.data.syscon_pwm_channels)
   *(.data.syscon_gpio_pins) *(.data.syscon_i2c_bus)
   *(.data.syscon_reset_cause_cache)
   *(.data.syscon_uart_ports)
   . = ALIGN(4); __peripheral_data_end = .;
 } > SRAM AT> CODE :peripherals
 __peripheral_data_load = LOADADDR(.peripheral_data);
 .peripheral_bss (NOLOAD) : {
   __peripheral_bss_start = .; *(.bss.syscon_rgb_runtime)
   . = ALIGN(4); __peripheral_bss_end = .;
 } > SRAM :peripheral_bss
 .irq_bss (NOLOAD) : {
   __irq_bss_start = .;
   *(.bss.syscon_gpio_handlers) *(.bss.syscon_i2c_state)
   *(.bss.syscon_uart_config) *(.bss.syscon_uart_rings)
   *(.bss.syscon_log_enabled)
   . = ALIGN(4); __irq_bss_end = .;
 } > SRAM :irq_state
 .power_data : ALIGN(4) {
   __power_data_start = .;
   *(.data.syscon_power_names)
   . = ALIGN(4); __power_data_end = .;
 } > SRAM AT> CODE :power_data
 __power_data_load = LOADADDR(.power_data);
 .power_bss (NOLOAD) : {
   __power_bss_start = .;
   *(.bss.syscon_shutdown_reason) *(.bss.syscon_usb_reattach_state)
   *(.bss.syscon_shutdown_state) *(.bss.syscon_diagnostics_state)
   *(.bss.syscon_protocol_debug) *(.bss.syscon_runtime_heap)
   . = ALIGN(4); __power_bss_end = .;
 } > SRAM :power_state
 .protocol_data : ALIGN(4) {
   __protocol_data_start = .; *(.data.syscon_console_parser) *(.data.syscon_modem_parser)
   . = ALIGN(4); __protocol_data_end = .;
 } > SRAM AT> CODE :protocol_data
 __protocol_data_load = LOADADDR(.protocol_data);
 .application_bss (NOLOAD) : {
   __application_bss_start = .;
   *(.bss.syscon_key_events) *(.bss.syscon_console_buffer)
   *(.bss.syscon_key_event_buffer) *(.bss.syscon_shutdown_pending)
   *(.bss.syscon_key_started_off) *(.bss.syscon_wakeup_pending)
   *(.bss.syscon_application_dso) *(.bss.syscon_ioexpander_initialized)
   . = ALIGN(4); __application_bss_end = .;
 } > SRAM :application_state
 .modem_bss (NOLOAD) : {
   __modem_bss_start = .;
   *(.bss.syscon_modem_runtime) *(.bss.syscon_modem_boot) *(.bss.syscon_modem_timing)
   *(.bss.syscon_modem_buffer) *(.bss.syscon_modem_scratch)
   __modem_bss_end = .;
 } > SRAM :modem_state
 .runtime_data : ALIGN(4) {
   __runtime_data_start = .; *(.data.syscon_runtime_context) *(.data.syscon_runtime_current)
   . = ALIGN(4); __runtime_data_end = .;
 } > SRAM AT> CODE :runtime_data
 __runtime_data_load = LOADADDR(.runtime_data);
 .data : ALIGN(4) {__data_start = .;*(.data*) . = ALIGN(4);__data_end = .;} > SRAM AT> CODE :initialized
 __data_load = LOADADDR(.data);
 .state_bss (NOLOAD) : {
   __state_bss_start = .;
   *(.bss.syscon_retained_state)
   *(.bss.syscon_timer_state) *(.bss.syscon_task_state)
   . = ALIGN(4); __state_bss_end = .;
 } > SRAM :state
 .extra_bss (NOLOAD) : {__extra_bss_start = .;*(.bss*) *(COMMON) .  =  ALIGN(4);__extra_bss_end = .;} > SRAM :auxiliary
 /DISCARD/ : {*(.comment) *(.note*) *(.ARM.attributes)}
 ASSERT(SIZEOF(.vectors)==192,"Vector table must contain48entries")
 ASSERT(__ram_exec_used_end>__ram_exec_start,"RAM executor missing")
 ASSERT(__ram_exec_used_end-__ram_exec_start<=48,"RAM executor exceeds original48byte slot")
 ASSERT(SIZEOF(.command_table)>0 && SIZEOF(.command_table)%14==0,"Command descriptors must be complete records")
 ASSERT(__extra_bss_end<=__stack_top-1024,"Less than1KiB stack remains; whole-image stack bound required")
 ASSERT((__data_load & 3)==0 && (__data_start & 3)==0 && (__data_end & 3)==0,"Reset data copy requires word alignment")
 ASSERT(SIZEOF(.data)==0 || __data_load+SIZEOF(.data)<=ORIGIN(CODE)+LENGTH(CODE),"Initialized data load image exceeds code region")
 ASSERT(SIZEOF(.version)<=8,"Version must not enter identity sector")
}
