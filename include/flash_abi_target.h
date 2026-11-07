#ifndef SYSCON_FLASH_ABI_TARGET_H
#define SYSCON_FLASH_ABI_TARGET_H
#include <stdint.h>
void syscon_target_flash_report(void); /* 2738 */
uint32_t syscon_target_flash_erase(uint32_t base,uint32_t address,uint32_t size); /* 7af4 */
uint32_t syscon_target_flash_program(uint32_t base,uint32_t address,uint32_t data); /* 7b10 */
uint32_t syscon_target_flash_unprotect(uint32_t base); /* 7b44; R0 preserved */
uint32_t syscon_target_flash_blank(uint32_t base,uint32_t address); /* 7b60 */
uint32_t syscon_target_flash_veneer(uint32_t base); /* aae0; linker-resolved RAM entry */
uint32_t syscon_target_flash_ram_execute(uint32_t base); /* copied to SRAM by reset */
#endif
