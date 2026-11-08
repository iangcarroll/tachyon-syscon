ENTRY(syscon_target_flash_ram_execute)
MEMORY {
 TEST_CODE (rx) : ORIGIN = 0x01000000, LENGTH = 512K
 TEST_DATA (rw) : ORIGIN = 0x21000000, LENGTH = 32K
 RAM_EXEC (rwx) : ORIGIN = 0x20000000, LENGTH = 48
}
SECTIONS {
 .ram_original_flash : {KEEP(*(.ram_original_flash))} > RAM_EXEC AT> TEST_CODE
 .text : {*(.text*) *(.rodata*)} > TEST_CODE
 .data : {*(.data*)} > TEST_DATA AT> TEST_CODE
 .bss (NOLOAD) : {*(.bss*) *(COMMON)} > TEST_DATA
 /DISCARD/ : {*(.comment) *(.note*)}
 ASSERT(SIZEOF(.ram_original_flash)<=48,"Original RAM slot overflow")
}
