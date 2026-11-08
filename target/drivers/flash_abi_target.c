#include "flash_abi_target.h"
#define W(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))
extern void syscon_target_logger(uint32_t, const char *, const char *, ...);
void syscon_target_flash_report(void)
{
    uint32_t value = W(0x400ce3d0u) & 0x10f0u;
    const char *message;
    switch (value) {
    case 0:
        message = "Flash: op success";
        break;
    case 0x10:
        message = "Flash: write/erase protect failure";
        break;
    case 0x20:
        message = "Flash: verify error failure";
        break;
    case 0x40:
        message = "Flash: illegal address failure";
        break;
    case 0x80:
        message = "Flash: wrong bank mode failure";
        break;
    case 0x1000:
        message = "Flash: undefined failure";
        break;
    default:
        message = "Flash: unknown failure";
        break;
    }
    syscon_target_logger(1, "CONF", message);
}
/* This original-ABI body is independent of the generic callback controller.
 * Placement in physical firmware requires a reviewed linker/reset change. */
__attribute__((section(".ram_original_flash"), noinline)) uint32_t
syscon_target_flash_ram_execute(uint32_t base)
{
    W(base + 0x1100u) = 1;
    uint32_t status;
    do {
        status = W(base + 0x13d0u) & 7u;
    } while (status != 1u && status != 3u);
    return status;
}
uint32_t syscon_target_flash_veneer(uint32_t base)
{
    return syscon_target_flash_ram_execute(base);
}
uint32_t syscon_target_flash_erase(uint32_t base, uint32_t address, uint32_t size)
{
    W(base + 0x1104u) = size | 2u;
    W(base + 0x1120u) = address;
    return syscon_target_flash_veneer(base);
}
uint32_t syscon_target_flash_program(uint32_t base, uint32_t address, uint32_t data)
{
    W(base + 0x1104u) = 1;
    W(base + 0x1124u) = 255;
    W(base + 0x1120u) = address;
    uint32_t word = W(data);
    W(base + 0x1130u) = word;
    word = W(data + 4u);
    W(base + 0x1134u) = word;
    return syscon_target_flash_veneer(base);
}
uint32_t syscon_target_flash_unprotect(uint32_t base)
{
    W(base + 0x11d0u) = 0;
    W(base + 0x11d4u) = 0;
    W(base + 0x11d8u) = 0;
    return base;
}
uint32_t syscon_target_flash_blank(uint32_t base, uint32_t address)
{
    W(base + 0x1104u) = 6;
    W(base + 0x1120u) = address;
    return syscon_target_flash_veneer(base);
}
