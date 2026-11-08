/* UART receive buffering and direct volatile peripheral operations. */
#include "uart_ring_target.h"
#include "uart_state.h"
#include "hal_helpers.h"
#include "runtime_memory.h"
#define U8(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))

static volatile syscon_uart_port_t *lookup_or_assert(uint32_t port, uint32_t line)
{
    volatile syscon_uart_port_t *descriptor =
        (volatile syscon_uart_port_t *)(uintptr_t)syscon_hal_uart_lookup(port);
    if (!descriptor) {
        syscon_target_assert((uint32_t)(uintptr_t)"hal_uart.cpp", line,
                             (uint32_t)(uintptr_t)"uart != nullptr");
    }
    return descriptor;
}
void syscon_target_uart_rx_disable(uint32_t port)
{
    volatile syscon_uart_port_t *descriptor =
        (volatile syscon_uart_port_t *)(uintptr_t)syscon_hal_uart_lookup(port);
    uint32_t base = descriptor->peripheral;
    uint32_t mask = U32(base + 0x1028u);
    U32(base + 0x1028u) = mask & ~UINT32_C(0x400);
}
void syscon_target_uart_rx_enable(uint32_t port)
{
    volatile syscon_uart_port_t *descriptor =
        (volatile syscon_uart_port_t *)(uintptr_t)syscon_hal_uart_lookup(port);
    uint32_t base = descriptor->peripheral;
    uint32_t mask = U32(base + 0x1028u);
    U32(base + 0x1028u) = mask | UINT32_C(0x400);
}
uint32_t syscon_target_uart_put(uint32_t port, uint32_t character)
{
    volatile syscon_uart_port_t *descriptor = lookup_or_assert(port, 0xae);
    if (!syscon_uart_config[port].mode)
        syscon_hal_uart_put_blocking(descriptor->peripheral, character);
    return 0;
}
uint32_t syscon_target_uart_write_buffer_body(uint32_t port, uint32_t data, uint32_t size)
{
    volatile syscon_uart_port_t *descriptor = lookup_or_assert(port, 0xb9);
    if (!syscon_uart_config[port].mode) {
        uint32_t end = data + size;
        while (data != end) {
            uint32_t character = U8(data);
            syscon_hal_uart_put_blocking(descriptor->peripheral, character);
            ++data;
        }
    }
    return 0;
}
uint32_t syscon_target_uart_available(uint32_t port)
{
    (void)lookup_or_assert(port, 0xc6);
    if (syscon_uart_config[port].mode)
        return 0;
    syscon_target_uart_rx_disable(port);
    volatile syscon_uart_ring_t *ring = &syscon_uart_rings[port];
    uint32_t write = ring->write_index;
    uint32_t read = ring->read_index;
    uint32_t full = ring->full;
    syscon_target_uart_rx_enable(port);
    if (full)
        return SYSCON_UART_RX_CAPACITY;
    if (write < read)
        write += SYSCON_UART_RX_CAPACITY;
    return write - read;
}
void syscon_target_uart_irq(uint32_t base)
{
    volatile syscon_uart_port_t *first =
        (volatile syscon_uart_port_t *)(uintptr_t)syscon_hal_uart_lookup(0);
    uint32_t first_match = first->peripheral == base;
    volatile syscon_uart_port_t *second =
        (volatile syscon_uart_port_t *)(uintptr_t)syscon_hal_uart_lookup(1);
    uint32_t port;
    if (second->peripheral == base)
        port = 1;
    else if (first_match)
        port = 0;
    else
        return;
    if ((uint8_t)U32(base + 0x1020u) != 11)
        return;
    uint8_t value = (uint8_t)U32(base + 0x1124u);
    if (syscon_target_uart_available(port) == SYSCON_UART_RX_CAPACITY)
        return;
    volatile syscon_uart_ring_t *ring = &syscon_uart_rings[port];
    uint32_t write = ring->write_index;
    U8((uint32_t)(uintptr_t)ring + write) = value;
    /* Original reloads after a possibly self-aliasing data write. */
    write = ring->write_index;
    ring->write_index = (write + 1u) & (SYSCON_UART_RX_CAPACITY - 1u);
    write = ring->write_index;
    uint32_t read = ring->read_index;
    if (write == read)
        ring->full = 1;
}
uint32_t syscon_target_uart_read(uint32_t port)
{
    (void)lookup_or_assert(port, 0xde);
    uint8_t disabled = syscon_uart_config[port].mode;
    if (disabled)
        return UINT32_MAX;
    if ((int32_t)syscon_target_uart_available(port) <= 0)
        return UINT32_MAX;
    syscon_target_uart_rx_disable(port);
    volatile syscon_uart_ring_t *ring = &syscon_uart_rings[port];
    uint32_t read = ring->read_index;
    uint32_t value = U8((uint32_t)(uintptr_t)ring + read);
    read = ring->read_index;
    ring->read_index = (read + 1u) & (SYSCON_UART_RX_CAPACITY - 1u);
    ring->full = disabled;
    syscon_target_uart_rx_enable(port);
    return value;
}
