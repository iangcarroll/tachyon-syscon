/* Physical geometry of the unconfirmed MSPM0L1306 profile; not flash approval. */
ENTRY(syscon_physical_reset)
MEMORY {
 CODE (rx) : ORIGIN = 0x00000000, LENGTH = 0xab20
 FIXED (r) : ORIGIN = 0xab20, LENGTH = 0x3a58
 SPARE (rx) : ORIGIN = 0xe578, LENGTH = 0x1280
 VERSION_REGION (r) : ORIGIN = 0xf7f8, LENGTH = 8
 IDENTITY (r) : ORIGIN = 0xf800, LENGTH = 0x400
 CONFIG (r) : ORIGIN = 0xfc00, LENGTH = 0x400
 RAM_EXEC (rwx) : ORIGIN = 0x20000000, LENGTH = 0x30
 RAM_FIXED (rw) : ORIGIN = 0x20000030, LENGTH = 0x7f0
 RAM_AUX (rwx) : ORIGIN = 0x20000820, LENGTH = 0x7e0
}
/* Separate PT_LOAD flags keep compatibility data out of executable ELF segments.
   The MCU does not acquire memory protection from ELF program headers. */
PHDRS {
 vectors PT_LOAD FLAGS(4);
 ram_exec PT_LOAD FLAGS(5);
 ram_extra PT_LOAD FLAGS(7);
 early PT_LOAD FLAGS(5);
 legacy PT_LOAD FLAGS(4);
 text PT_LOAD FLAGS(5);
 fixed PT_LOAD FLAGS(4);
 config_data PT_LOAD FLAGS(4);
 version PT_LOAD FLAGS(4);
 auxiliary PT_LOAD FLAGS(6);
 initialized PT_LOAD FLAGS(6);
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
 .fixed_actions 0xab20 : {KEEP(*(.fixed.ab20))} > FIXED :fixed
 .command_table 0xc419 : {KEEP(*(.rodata.syscon_target_commands))} > FIXED :fixed
 .fixed_strings 0xc61f : {KEEP(*(.fixed.c61f))} > FIXED :fixed
 .constructors 0xe2d8 : {KEEP(*(.physical.constructors))} > FIXED :fixed
 .initial_data 0xe2e8 : {__physical_initial_data = .;KEEP(*(.physical.initial_data))} > FIXED :fixed
 .version 0xf7f8 : {KEEP(*(.physical.version))} > VERSION_REGION :version
 .text_early : {
   *target_callback_helpers.o(.text*)
   *target_config_helpers.o(.text*)
   *target_config_read.o(.text*)
   *target_config_storage.o(.text*)
   *target_config_write_slot_abi.o(.text*)
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
 /* Legacy missing %s vararg is the numeric original LR 0x2919.
    Preserve only its observed NUL data byte, never original instructions. */
 .legacy_format_nul 0x2919 (READONLY) : { BYTE(0) } > CODE :legacy
 /* Configuration constants are independently relocatable C data. Other modules
    still use recovered fixed data until their own source migration. */
 .config_data : { *target_config*.o(.rodata*) } > SPARE :config_data
 .text : { *(.text*) *(.rodata*) } > CODE :text
 .ARM.exidx : {* (.ARM.exidx*)} > CODE :text
 .data : ALIGN(4) {__data_start = .;*(.data*) . = ALIGN(4);__data_end = .;} > RAM_AUX AT> CODE :initialized
 __data_load = LOADADDR(.data);
 .extra_bss (NOLOAD) : {__extra_bss_start = .;*(.bss*) *(COMMON) .  =  ALIGN(4);__extra_bss_end = .;} > RAM_AUX :auxiliary
 /DISCARD/ : {*(.comment) *(.note*) *(.ARM.attributes)}
 ASSERT(ADDR(.text_early)+SIZEOF(.text_early)<=0x2919,"Early text overlaps legacy format NUL")
 ASSERT(ADDR(.legacy_format_nul)==0x2919 && SIZEOF(.legacy_format_nul)==1,"Legacy format NUL must remain one byte at2919")
 ASSERT(SIZEOF(.vectors)==192,"Vector table must contain48entries")
 ASSERT(__ram_exec_used_end>__ram_exec_start,"RAM executor missing")
 ASSERT(__ram_exec_used_end-__ram_exec_start<=48,"RAM executor exceeds original48byte slot")
 ASSERT(SIZEOF(.command_table)==518,"Command descriptor layout must remain37x14")
 ASSERT(SIZEOF(.constructors)==8,"Constructor list must contain2source pointers")
 ASSERT(SIZEOF(.initial_data)==656,"Initialized RAM image must remain656bytes")
 ASSERT(__extra_bss_end<=0x20000c00,"Less than1KiB stack remains; whole-image stack bound required")
 ASSERT((__data_load & 3)==0 && (__data_start & 3)==0 && (__data_end & 3)==0,"Reset data copy requires word alignment")
 ASSERT(SIZEOF(.data)==0 || __data_load+SIZEOF(.data)<=ORIGIN(CODE)+LENGTH(CODE),"Initialized data load image exceeds code region")
 ASSERT(SIZEOF(.version)<=8,"Version must not enter identity sector")
}
