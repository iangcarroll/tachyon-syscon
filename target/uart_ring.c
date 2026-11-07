/* Direct original ARM ABI and memory layout, including unchecked ring indices. */
#include "uart_ring_target.h"
#include "hal_helpers.h"
#include "runtime_memory.h"
#define U8(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))

static uint32_t lookup_or_assert(uint32_t port, uint32_t line) {
    uint32_t descriptor = syscon_hal_uart_lookup(port);
    if (!descriptor) {
        uint32_t file = UINT32_C(0xe0af);
        if (syscon_rt_strrchr((const void *)(uintptr_t)file, '/'))
            file = (uint32_t)(uintptr_t)syscon_rt_strrchr((const void *)(uintptr_t)file, '/') + 1u;
        syscon_target_assert(file, line, UINT32_C(0xcfb8));
    }
    return descriptor;
}
void syscon_target_uart_rx_disable(uint32_t port) {
    uint32_t descriptor = syscon_hal_uart_lookup(port);
    uint32_t base = U32(descriptor + 8u);
    uint32_t mask = U32(base + 0x1028u);
    U32(base + 0x1028u) = mask & ~UINT32_C(0x400);
}
void syscon_target_uart_rx_enable(uint32_t port) {
    uint32_t descriptor = syscon_hal_uart_lookup(port);
    uint32_t base = U32(descriptor + 8u);
    uint32_t mask = U32(base + 0x1028u);
    U32(base + 0x1028u) = mask | UINT32_C(0x400);
}
uint32_t syscon_target_uart_put(uint32_t port, uint32_t character) {
    uint32_t descriptor = lookup_or_assert(port, 0xae);
    if (!U8(0x20000762u + port*9u + 8u))
        syscon_hal_uart_put_blocking(U32(descriptor + 8u), character);
    return 0;
}
uint32_t syscon_target_uart_write_buffer_body(uint32_t port, uint32_t data, uint32_t size) {
    uint32_t descriptor = lookup_or_assert(port, 0xb9);
    if (!U8(0x20000762u + port*9u + 8u)) {
        uint32_t end = data + size;
        while (data != end) {
            uint32_t character = U8(data);
            syscon_hal_uart_put_blocking(U32(descriptor + 8u), character);
            ++data;
        }
    }
    return 0;
}
uint32_t syscon_target_uart_available(uint32_t port) {
    (void)lookup_or_assert(port, 0xc6);
    if (U8(0x20000762u + port*9u + 8u)) return 0;
    syscon_target_uart_rx_disable(port);
    uint32_t ring = 0x20000774u + port*0x4cu;
    uint32_t write = U32(ring + 0x40u);
    uint32_t read = U32(ring + 0x44u);
    uint32_t full = U8(ring + 0x48u);
    syscon_target_uart_rx_enable(port);
    if (full) return 64;
    if (write < read) write += 64;
    return write - read;
}
void syscon_target_uart_irq(uint32_t base) {
    uint32_t first = syscon_hal_uart_lookup(0);
    uint32_t first_match = U32(first + 8u) == base;
    uint32_t second = syscon_hal_uart_lookup(1);
    uint32_t port;
    if (U32(second + 8u) == base) port = 1;
    else if (first_match) port = 0;
    else return;
    if ((uint8_t)U32(base + 0x1020u) != 11) return;
    uint8_t value = (uint8_t)U32(base + 0x1124u);
    if (syscon_target_uart_available(port) == 64) return;
    uint32_t ring = 0x20000774u + port*0x4cu;
    uint32_t write = U32(ring + 0x40u);
    U8(ring + write) = value;
    /* Original reloads after a possibly self-aliasing data write. */
    write = U32(ring + 0x40u);
    U32(ring + 0x40u) = (write + 1u) & 63u;
    write = U32(ring + 0x40u);
    uint32_t read = U32(ring + 0x44u);
    if (write == read) U8(ring + 0x48u) = 1;
}
uint32_t syscon_target_uart_read(uint32_t port) {
    (void)lookup_or_assert(port, 0xde);
    uint8_t disabled = U8(0x20000762u + port*9u + 8u);
    if (disabled) return UINT32_MAX;
    if ((int32_t)syscon_target_uart_available(port) <= 0) return UINT32_MAX;
    syscon_target_uart_rx_disable(port);
    uint32_t ring = 0x20000774u + port*0x4cu;
    uint32_t read = U32(ring + 0x44u);
    uint32_t value = U8(ring + read);
    read = U32(ring + 0x44u);
    U32(ring + 0x44u) = (read + 1u) & 63u;
    U8(ring + 0x48u) = disabled;
    syscon_target_uart_rx_enable(port);
    return value;
}
