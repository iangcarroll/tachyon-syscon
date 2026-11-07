ENTRY(syscon_checksum31)
SECTIONS { . = 0x01000000; .text : { *(.text.syscon_checksum31) } /DISCARD/ : { *(.ARM.exidx*) *(.comment*) } }
