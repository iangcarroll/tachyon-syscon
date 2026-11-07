#ifndef SYSCON_FLASH_CONTROLLER_H
#define SYSCON_FLASH_CONTROLLER_H
#include <stdint.h>
typedef struct {
    void *context;
    uint32_t (*read)(void *,uint32_t);
    void (*write)(void *,uint32_t,uint32_t);
} syscon_flash_controller_io;
/* Original RAM routine: no timeout; only masked statuses 1 and 3 terminate. */
uint32_t syscon_flash_execute(const syscon_flash_controller_io *,uint32_t base);
uint32_t syscon_flash_erase(const syscon_flash_controller_io *,uint32_t base,uint32_t address,uint32_t size);
uint32_t syscon_flash_program(const syscon_flash_controller_io *,uint32_t base,uint32_t address,const uint8_t data[8]);
uint32_t syscon_flash_blank(const syscon_flash_controller_io *,uint32_t base,uint32_t address);
void syscon_flash_unprotect_main(const syscon_flash_controller_io *,uint32_t base);
typedef void (*syscon_flash_reporter)(void *,unsigned level,const char *tag,const char *message);
void syscon_flash_report(const syscon_flash_controller_io *,uint32_t base,syscon_flash_reporter,void *);
#endif
