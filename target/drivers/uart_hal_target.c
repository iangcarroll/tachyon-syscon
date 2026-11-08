#include "uart_hal_target.h"
#include "uart_state.h"
#include "hal_helpers.h"
#include "mspm0_core_target.h"
#include "runtime_memory.h"
#include "runtime_arithmetic.h"
#define U8(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define U16(a) (*(volatile uint16_t *)(uintptr_t)(uint32_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))
extern float __aeabi_ui2f(uint32_t);
extern float __aeabi_i2f(int32_t);
extern float __aeabi_fsub(float, float);
extern float __aeabi_fmul(float, float);
extern double __aeabi_f2d(float);
extern double __aeabi_dadd(double, double);
extern uint32_t syscon_rt_f2u(uint32_t);
extern uint32_t syscon_rt_d2u(uint64_t);
static void uart_assert(uint32_t line, const char *expression)
{
    syscon_target_assert((uint32_t)(uintptr_t)"hal_uart.cpp", line,
                         (uint32_t)(uintptr_t)expression);
}
void syscon_target_uart_clock_config(uint32_t base, uint32_t config)
{
    uint32_t source = U8(config);
    U32(base + 0x1008u) = source;
    uint32_t divider = U8(config + 1u);
    U32(base + 0x1000u) = divider;
}
void syscon_target_uart_line_config(uint32_t base, uint32_t config)
{
    uint32_t old = U32(base + 0x1100u);
    U32(base + 0x1100u) = old & ~1u;
    uint32_t byte2 = U8(config + 2u);
    uint32_t half0 = U16(config);
    old = U32(base + 0x1100u);
    uint32_t half4 = U16(config + 4u);
    U32(base + 0x1100u) = old ^ ((old ^ (byte2 | half0 | half4)) & 0x26718u);
    uint32_t byte7 = U8(config + 7u), byte6 = U8(config + 6u), byte8 = U8(config + 8u);
    old = U32(base + 0x1104u);
    U32(base + 0x1104u) = old ^ ((old ^ (byte7 | byte6 | byte8)) & 0x7eu);
}
uint32_t syscon_target_uart_init(uint32_t port, uint32_t config)
{
    volatile syscon_uart_port_t *descriptor =
        (volatile syscon_uart_port_t *)(uintptr_t)syscon_hal_uart_lookup(port);
    if (!descriptor)
        uart_assert(0x5bu, "uart != nullptr");
    if (!config)
        uart_assert(0x5cu, "config != nullptr");
    uint32_t tx = syscon_target_gpio_lookup(descriptor->tx_pin);
    uint32_t rx = syscon_target_gpio_lookup(descriptor->rx_pin);
    uint32_t mux = U8(tx + 5u), function = descriptor->tx_function;
    U32(0x40428004u + mux * 4u) = function | 0x80u;
    mux = U8(rx + 5u);
    function = descriptor->rx_function;
    U32(0x40428004u + mux * 4u) = function | 0x40080u;
    uint32_t base = descriptor->peripheral;
    U32(base + 0x804u) = 0xb1000003u;
    U32(base + 0x800u) = 0x26000001u;
    uint8_t clock[2] = {8, 0};
    syscon_target_uart_clock_config(base, (uint32_t)(uintptr_t)clock);
    /* Recovered line configuration: preserve every byte, including padding. */
    static const uint8_t default_line[10] = {0, 0, 0x18, 0, 0, 0, 0, 0x30, 0, 0};
    uint8_t line[sizeof(default_line)];
    syscon_rt_memcpy(line, default_line, sizeof(line));
    base = descriptor->peripheral;
    syscon_target_uart_line_config(base, (uint32_t)(uintptr_t)line);
    base = descriptor->peripheral;
    uint32_t old = U32(base + 0x1100u);
    U32(base + 0x1100u) = old & 0xfffe7fffu;
    uint32_t b5 = U8(config + 5u), b4 = U8(config + 4u), b6 = U8(config + 6u), b7 = U8(config + 7u);
    uint32_t baud = b4 | (b5 << 8) | (b6 << 16) | (b7 << 24);
    uint32_t quotient = (uint32_t)syscon_rt_udiv32(2000000u, baud);
    union {
        float f;
        uint32_t u;
    } q = {.f = __aeabi_ui2f(quotient)};
    uint32_t integer = (uint16_t)syscon_rt_f2u(q.u);
    old = U32(base + 0x1110u);
    U32(base + 0x1110u) = old ^ ((old ^ integer) & 0xffffu);
    uint32_t fractional_old = U32(base + 0x1114u);
    float remaining = __aeabi_fsub(q.f, __aeabi_i2f((int32_t)integer));
    float scaled = __aeabi_fmul(remaining, 64.0f);
    union {
        double d;
        uint64_t u;
    } rounded = {.d = __aeabi_dadd(__aeabi_f2d(scaled), 0.5)};
    uint32_t fractional = (uint16_t)syscon_rt_d2u(rounded.u);
    U32(base + 0x1114u) = fractional_old ^ ((fractional_old ^ fractional) & 63u);
    uint32_t first = U32(base + 0x1104u), second = U32(base + 0x1104u);
    U32(base + 0x1104u) = (first & 1u) | (second & ~1u);
    if (!U8(config + 8u)) {
        old = U32(base + 0x1028u);
        U32(base + 0x1028u) = old | 0x400u;
        uint32_t irq = descriptor->irq;
        if (irq < 128u) {
            uint32_t mask = 1u << (irq & 31u);
            U32(0xe000e280u) = mask;
            U32(0xe000e100u) = mask;
        }
    }
    base = descriptor->peripheral;
    old = U32(base + 0x1100u);
    U32(base + 0x1100u) = old | 1u;
    uint32_t low = U8(config + 2u), high = U8(config + 3u), count = low | (high << 8);
    if (count >= sizeof(syscon_uart_config[port]))
        count = sizeof(syscon_uart_config[port]);
    syscon_rt_memcpy((void *)&syscon_uart_config[port], (const void *)(uintptr_t)config, count);
    syscon_rt_memset((void *)&syscon_uart_rings[port], 0, sizeof(syscon_uart_rings[port]));
    return 0;
}
uint32_t syscon_target_uart_deinit(uint32_t port)
{
    volatile syscon_uart_port_t *descriptor =
        (volatile syscon_uart_port_t *)(uintptr_t)syscon_hal_uart_lookup(port);
    if (!descriptor)
        uart_assert(0x96u, "uart != nullptr");
    uint32_t irq = descriptor->irq;
    if (irq < 128u) {
        U32(0xe000e180u) = 1u << (irq & 31u);
        __asm__ volatile("dsb sy\nisb sy" ::: "memory");
    }
    uint32_t base = descriptor->peripheral;
    uint32_t old = U32(base + 0x1028u);
    U32(base + 0x1028u) = old & ~0x400u;
    irq = descriptor->irq;
    if (irq < 128u)
        U32(0xe000e280u) = 1u << (irq & 31u);
    old = U32(base + 0x1100u);
    U32(base + 0x1100u) = old & ~1u;
    uint32_t txpin = descriptor->tx_pin;
    U32(base + 0x804u) = 0xb1000003u;
    U32(base + 0x800u) = 0x26000000u;
    uint32_t tx = syscon_target_gpio_lookup(txpin);
    uint32_t rx = syscon_target_gpio_lookup(descriptor->rx_pin);
    uint32_t mux = U8(tx + 5u), function = descriptor->tx_idle_function;
    U32(0x40428004u + mux * 4u) = function | 0x80u;
    mux = U8(rx + 5u);
    function = descriptor->rx_idle_function;
    U32(0x40428004u + mux * 4u) = function | 0x40080u;
    return 0;
}
