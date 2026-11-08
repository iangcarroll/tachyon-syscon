/* Physical geometry of the unconfirmed MSPM0L1306 profile; not flash approval. */
ENTRY(syscon_physical_reset)
MEMORY {
 CODE (rx) : ORIGIN = 0x00000000, LENGTH = 0xab20
 FIXED (r) : ORIGIN = 0xab20, LENGTH = 0x3a58
 /* Migrated power strings/scales no longer occupy their original ROM block. */
 RECLAIMED_TEXT (r) : ORIGIN = 0xab20, LENGTH = 0x37b8
 SPARE (rx) : ORIGIN = 0xe578, LENGTH = 0x1280
 VERSION_REGION (r) : ORIGIN = 0xf7f8, LENGTH = 8
 IDENTITY (r) : ORIGIN = 0xf800, LENGTH = 0x400
 CONFIG (r) : ORIGIN = 0xfc00, LENGTH = 0x400
 RAM_EXEC (rwx) : ORIGIN = 0x20000000, LENGTH = 0x30
 RAM_FIXED (rw) : ORIGIN = 0x20000030, LENGTH = 0x7f0
 /* Reuse the now-vacant task/timer SRAM instead of reserving a second copy.
    This partition is transitional until remaining fixed-state users migrate. */
 RAM_STATE (rw) : ORIGIN = 0x20000534, LENGTH = 0x14c
 /* Former ADC/I2C/PWM/GPIO/UART descriptors are now one allocation arena. */
 RAM_PERIPHERALS (rw) : ORIGIN = 0x200000f4, LENGTH = 0x164
 /* Reclaimed ADC scratch, GPIO callbacks and UART receive state, below logging state. */
 RAM_IRQ_STATE (rw) : ORIGIN = 0x20000684, LENGTH = 0x188
 /* Reclaim old power-name tables and migrated power/key/RGB state. */
 RAM_POWER_DATA (rw) : ORIGIN = 0x20000370, LENGTH = 0x54
 RAM_POWER_STATE (rw) : ORIGIN = 0x2000005c, LENGTH = 0x58
 RAM_PROTOCOL_DATA (rw) : ORIGIN = 0x20000030, LENGTH = 0x2c
 RAM_APPLICATION (rw) : ORIGIN = 0x200002c0, LENGTH = 0xb0
 RAM_MODEM (rw) : ORIGIN = 0x200003c4, LENGTH = 0x170
 RAM_LIBC (rw) : ORIGIN = 0x20000258, LENGTH = 0x68
 RAM_AUX (rwx) : ORIGIN = 0x20000820, LENGTH = 0x7e0
}
/* Separate PT_LOAD flags distinguish code and read-only data in the ELF.
   The MCU does not acquire memory protection from ELF program headers. */
PHDRS {
 vectors PT_LOAD FLAGS(4);
 ram_exec PT_LOAD FLAGS(5);
 ram_extra PT_LOAD FLAGS(7);
 early PT_LOAD FLAGS(5);
 text PT_LOAD FLAGS(5);
 fixed PT_LOAD FLAGS(4);
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
 } > RAM_EXEC AT> CODE :ram_exec
 __ram_exec_load = LOADADDR(.ram_exec);
 .ram_extra : {
   __ram_extra_start = .;
   /* Additional RAM sections require explicit review; direct flash needs none. */
   .  =  ALIGN(4);__ram_extra_end = .;
 } > RAM_AUX AT> CODE :ram_extra
 __ram_extra_load = LOADADDR(.ram_extra);
 .command_table : {KEEP(*(.rodata.syscon_target_commands))} > RECLAIMED_TEXT :application_rodata
 .constructors 0xe2d8 : {KEEP(*(.physical.constructors))} > FIXED :fixed
 .initial_data 0xe2e8 : {__physical_initial_data = .;KEEP(*(.physical.initial_data))} > FIXED :fixed
 .version 0xf7f8 : {KEEP(*(.physical.version))} > VERSION_REGION :version
 .text_early : {
   *target_callback_helpers.o(.text*)
   *target_config_helpers.o(.text*)
   *target_config_read.o(.text*)
   *target_config_storage.o(.text*)
   *target_core_helpers.o(.text*)
   *target_interface_bindings.o(.text*)
   *target_fault_control_target.o(.text*)
   *target_fault_handlers.o(.text*)
   *target_hal_helpers.o(.text*)
   *target_mspm0_core_target.o(.text*)
   *target_uart_ring.o(.text*)
   *target_runtime_arithmetic_abi.o(.text*)
   *target_runtime_heap.o(.text*)
   *target_runtime_scan.o(.text*)
   *target_runtime_scan_abi.o(.text*)
   *target_runtime_scan_printf.o(.text*)
   *target_runtime_scan_wrappers.o(.text*)
   *target_runtime_stdio.o(.text*)
   *target_runtime_support.o(.text*)
   *target_runtime_arithmetic_float.o(.text*)
 } > CODE :early
 /* Configuration constants are independently relocatable C data. Other modules
    still use recovered fixed data until their own source migration. */
 .config_data : { *target_config*.o(.rodata*) } > SPARE :config_data
 .peripheral_rodata : {
   *target_mspm0_core_target.o(.rodata*)
   *target_fault_control_target.o(.rodata*)
   *target_i2c_target.o(.rodata*)
   *target_uart_hal_target.o(.rodata*) *target_uart_ring.o(.rodata*)
   *target_power_manager_target.o(.rodata*) *target_power_policy_target.o(.rodata*)
   *target_power_state.o(.rodata*)
 } > SPARE :peripheral_rodata
 .application_rodata : {
   *target_core_helpers.o(.rodata*) *target_flash_abi_target.o(.rodata*)
   *target_ioexpander_target.o(.rodata*)
   *target_retained_target.o(.rodata*) *target_tasks_target.o(.rodata*) *target_timers_target.o(.rodata*)
   *target_runtime_state.o(.rodata*)
   *target_modem_state.o(.rodata*)
   *target_diagnostics_target.o(.rodata*)
   *target_sg560d_target.o(.rodata*)
   *target_application_target.o(.rodata*)
   *target_command_table_target.o(.rodata*)
   *target_protocol_target.o(.rodata*)
   *target_control_commands_target.o(.rodata*)
 } > RECLAIMED_TEXT :application_rodata
 .text : { *(.text*) *(.rodata*) } > CODE :text
 .ARM.exidx : {* (.ARM.exidx*)} > CODE :text
 .peripheral_data : ALIGN(4) {
   __peripheral_data_start = .; *(.data.syscon_pwm_channels)
   *(.data.syscon_gpio_pins) *(.data.syscon_i2c_bus)
   *(.data.syscon_reset_cause_cache)
   *(.data.syscon_uart_ports)
   . = ALIGN(4); __peripheral_data_end = .;
 } > RAM_PERIPHERALS AT> CODE :peripherals
 __peripheral_data_load = LOADADDR(.peripheral_data);
 .peripheral_bss (NOLOAD) : {
   __peripheral_bss_start = .; *(.bss.syscon_rgb_runtime)
   . = ALIGN(4); __peripheral_bss_end = .;
 } > RAM_PERIPHERALS :peripheral_bss
 .irq_bss (NOLOAD) : {
   __irq_bss_start = .;
   *(.bss.syscon_gpio_handlers) *(.bss.syscon_i2c_state)
   *(.bss.syscon_uart_config) *(.bss.syscon_uart_rings)
   *(.bss.syscon_log_enabled)
   . = ALIGN(4); __irq_bss_end = .;
 } > RAM_IRQ_STATE :irq_state
 .power_data : ALIGN(4) {
   __power_data_start = .;
   *(.data.syscon_power_names)
   . = ALIGN(4); __power_data_end = .;
 } > RAM_POWER_DATA AT> CODE :power_data
 __power_data_load = LOADADDR(.power_data);
 .power_bss (NOLOAD) : {
   __power_bss_start = .;
   *(.bss.syscon_shutdown_reason) *(.bss.syscon_usb_reattach_state)
   *(.bss.syscon_shutdown_state) *(.bss.syscon_diagnostics_state)
   *(.bss.syscon_protocol_debug) *(.bss.syscon_runtime_heap)
   . = ALIGN(4); __power_bss_end = .;
 } > RAM_POWER_STATE :power_state
 .protocol_data : ALIGN(4) {
   __protocol_data_start = .; *(.data.syscon_console_parser) *(.data.syscon_modem_parser)
   . = ALIGN(4); __protocol_data_end = .;
 } > RAM_PROTOCOL_DATA AT> CODE :protocol_data
 __protocol_data_load = LOADADDR(.protocol_data);
 .application_bss (NOLOAD) : {
   __application_bss_start = .;
   *(.bss.syscon_key_events) *(.bss.syscon_console_buffer)
   *(.bss.syscon_key_event_buffer) *(.bss.syscon_shutdown_pending)
   *(.bss.syscon_key_started_off) *(.bss.syscon_wakeup_pending)
   *(.bss.syscon_application_dso) *(.bss.syscon_ioexpander_initialized)
   . = ALIGN(4); __application_bss_end = .;
 } > RAM_APPLICATION :application_state
 .modem_bss (NOLOAD) : {
   __modem_bss_start = .;
   *(.bss.syscon_modem_runtime) *(.bss.syscon_modem_boot) *(.bss.syscon_modem_timing)
   *(.bss.syscon_modem_buffer) *(.bss.syscon_modem_scratch)
   __modem_bss_end = .;
 } > RAM_MODEM :modem_state
 .runtime_data : ALIGN(4) {
   __runtime_data_start = .; *(.data.syscon_runtime_context) *(.data.syscon_runtime_current)
   . = ALIGN(4); __runtime_data_end = .;
 } > RAM_LIBC AT> CODE :runtime_data
 __runtime_data_load = LOADADDR(.runtime_data);
 .data : ALIGN(4) {__data_start = .;*(.data*) . = ALIGN(4);__data_end = .;} > RAM_AUX AT> CODE :initialized
 __data_load = LOADADDR(.data);
 .state_bss ORIGIN(RAM_STATE) (NOLOAD) : {
   __state_bss_start = .;
   *(.bss.syscon_retained_state)
   *(.bss.syscon_timer_state) *(.bss.syscon_task_state)
   . = ALIGN(4); __state_bss_end = .;
 } > RAM_STATE :state
 .extra_bss (NOLOAD) : {__extra_bss_start = .;*(.bss*) *(COMMON) .  =  ALIGN(4);__extra_bss_end = .;} > RAM_AUX :auxiliary
 /DISCARD/ : {*(.comment) *(.note*) *(.ARM.attributes)}
 ASSERT(SIZEOF(.vectors)==192,"Vector table must contain48entries")
 ASSERT(__ram_exec_used_end>__ram_exec_start,"RAM executor missing")
 ASSERT(__ram_exec_used_end-__ram_exec_start<=48,"RAM executor exceeds original48byte slot")
 ASSERT(SIZEOF(.command_table)>0 && SIZEOF(.command_table)%14==0,"Command descriptors must be complete records")
 ASSERT(SIZEOF(.constructors)==8,"Constructor list must contain2source pointers")
 ASSERT(SIZEOF(.initial_data)==656,"Initialized RAM image must remain656bytes")
 ASSERT(__extra_bss_end<=0x20000c00,"Less than1KiB stack remains; whole-image stack bound required")
 ASSERT((__data_load & 3)==0 && (__data_start & 3)==0 && (__data_end & 3)==0,"Reset data copy requires word alignment")
 ASSERT(SIZEOF(.data)==0 || __data_load+SIZEOF(.data)<=ORIGIN(CODE)+LENGTH(CODE),"Initialized data load image exceeds code region")
 ASSERT(SIZEOF(.version)<=8,"Version must not enter identity sector")
}
