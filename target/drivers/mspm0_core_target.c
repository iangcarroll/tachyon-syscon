/* GPIO routing, interrupt dispatch and reset/watchdog control. */
#include "mspm0_core_target.h"
#include "gpio_state.h"
#include "runtime_memory.h"
#define U8(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))

static uint32_t arm_lsl(uint32_t value, uint32_t shift)
{
    shift &= 255u;
    return shift < 32u ? value << shift : 0;
}
static void gpio_assert(uint32_t line, const char *expression)
{
    syscon_target_assert((uint32_t)(uintptr_t)"hal_gpio.cpp", line,
                         (uint32_t)(uintptr_t)expression);
}

uint32_t syscon_target_watchdog_init(void)
{
    U32(0x40080804u) = 0xb1000003u;
    U32(0x40080800u) = 0x26000001u;
    U32(0x40081104u) = 0xbe000000u;
    U32(0x40081100u) = 0xc9020033u;
    U32(0x40081108u) = 0xa7u;
    return 0;
}
uint32_t syscon_target_watchdog_feed(void)
{
    U32(0x40081108u) = 0xa7u;
    return 0;
}
void syscon_target_hal_noop(void)
{
}
uint32_t syscon_target_gpio_lookup(uint32_t pin)
{
    return pin < SYSCON_GPIO_COUNT ? (uint32_t)(uintptr_t)&syscon_gpio_pins[pin] : 0;
}
uint32_t syscon_target_reset_cause(void)
{
    uint32_t cause = syscon_reset_cause_cache;
    if (cause == 255u) {
        cause = U32(0x400b0220u) & 31u;
        syscon_reset_cause_cache = (uint8_t)cause;
    }
    uint32_t index = (cause - 1u) & 255u;
    /* SYSCTL reset causes map into the protocol's seven reason IDs. */
    static const uint8_t reasons[] = {1, 5, 3, 0, 6, 3, 3, 3, 3, 3, 3,
                                      3, 3, 2, 3, 3, 3, 3, 2, 4, 4};
    return index < sizeof(reasons) ? reasons[index] : 3u;
}
uint32_t syscon_target_reset_cause_name(uint32_t cause)
{
    static const char *const names[] = {"BOR",       "POR",   "WDT", "SOFT_RESET", "HARDWARE_FAULT",
                                        "PIN_RESET", "WAKEUP"};
    return (uint32_t)(uintptr_t)(cause < 7u ? names[cause] : "UNKNOWN");
}
uint32_t syscon_target_gpio_config(uint32_t pin, uint32_t config)
{
    if (!config)
        gpio_assert(0x21u, "config != nullptr");
    if (pin >= SYSCON_GPIO_COUNT)
        gpio_assert(0x22u, "pin < HAL_PLATFORM_PIN_NUM");
    volatile syscon_gpio_pin_t *descriptor =
        (volatile syscon_gpio_pin_t *)(uintptr_t)syscon_target_gpio_lookup((uint8_t)pin);
    uint32_t physical = descriptor->physical_pin;
    uint32_t mask = arm_lsl(1u, physical);
    uint32_t port = descriptor->port;
    U32(port + 0x800u) = 0x26000001u;
    uint32_t mode = U8(config + 4u);
    if (!mode) {
        U32(port + 0x12e0u) = mask;
        uint32_t mux = descriptor->mux_index;
        uint32_t pull = U8(config + 5u);
        uint32_t address = 0x40428004u + mux * 4u;
        if (pull == 1u)
            U32(address) = 0xe0081u;
        else if (pull == 2u)
            U32(address) = 0xd0081u;
        else {
            U32(address) = 0x40081u;
            uint32_t old = U32(address);
            U32(address) = old | 0x2000000u;
        }
    } else if (mode == 1u) {
        uint32_t mux = descriptor->mux_index;
        U32(0x40428004u + mux * 4u) = 0x81u;
        uint32_t flags = U32(config + 8u);
        if (flags & 2u) {
            uint32_t value = U8(config + 7u);
            U32(port + (value ? 0x1290u : 0x12a0u)) = mask;
        }
        U32(port + 0x12d0u) = mask;
    }
    return 0;
}
uint32_t syscon_target_gpio_write(uint32_t pin, uint32_t value)
{
    if (pin >= SYSCON_GPIO_COUNT)
        gpio_assert(0x61u, "pin < HAL_PLATFORM_PIN_NUM");
    volatile syscon_gpio_pin_t *descriptor =
        (volatile syscon_gpio_pin_t *)(uintptr_t)syscon_target_gpio_lookup((uint8_t)pin);
    uint32_t physical = descriptor->physical_pin;
    uint32_t mask = arm_lsl(1u, physical);
    uint32_t port = descriptor->port;
    U32(port + (value ? 0x1290u : 0x12a0u)) = mask;
    return 0;
}
uint32_t syscon_target_gpio_toggle(uint32_t pin)
{
    if (pin >= SYSCON_GPIO_COUNT)
        gpio_assert(0x6du, "pin < HAL_PLATFORM_PIN_NUM");
    volatile syscon_gpio_pin_t *descriptor =
        (volatile syscon_gpio_pin_t *)(uintptr_t)syscon_target_gpio_lookup((uint8_t)pin);
    uint32_t physical = descriptor->physical_pin;
    uint32_t port = descriptor->port;
    U32(port + 0x12b0u) = arm_lsl(1u, physical);
    return 0;
}
uint32_t syscon_target_gpio_read(uint32_t pin)
{
    if (pin >= SYSCON_GPIO_COUNT)
        gpio_assert(0x74u, "pin < HAL_PLATFORM_PIN_NUM");
    volatile syscon_gpio_pin_t *descriptor =
        (volatile syscon_gpio_pin_t *)(uintptr_t)syscon_target_gpio_lookup((uint8_t)pin);
    uint32_t port = descriptor->port;
    uint32_t input = U32(port + 0x1380u);
    uint32_t physical = descriptor->physical_pin;
    return (input & arm_lsl(1u, physical)) != 0;
}
uint64_t syscon_target_gpio_attach(uint32_t pin, uint32_t edge, uint32_t callback, uint32_t context)
{
    if (pin >= SYSCON_GPIO_COUNT)
        gpio_assert(0x7au, "pin < HAL_PLATFORM_PIN_NUM");
    volatile syscon_gpio_pin_t *descriptor =
        (volatile syscon_gpio_pin_t *)(uintptr_t)syscon_target_gpio_lookup((uint8_t)pin);
    uint32_t physical = descriptor->physical_pin;
    syscon_gpio_handlers[pin].callback = callback;
    uint32_t mask = arm_lsl(1u, physical);
    syscon_gpio_handlers[pin].context = context;
    if (edge != 1u && edge != 2u)
        edge = 3u;
    uint32_t port = descriptor->port;
    uint32_t reg = port + (physical < 16u ? 0x1390u : 0x13a0u);
    uint32_t shift = (physical < 16u ? physical : physical - 16u) * 2u;
    uint32_t field = arm_lsl(3u, shift);
    uint32_t selected = arm_lsl(edge, shift);
    uint32_t old = U32(reg);
    U32(reg) = old & ~field;
    old = U32(reg);
    U32(reg) = old | selected;
    old = U32(port + 0x1048u);
    U32(port + 0x1048u) = old | mask;
    old = U32(port + 0x1028u);
    U32(port + 0x1028u) = old | mask;
    U32(0xe000e100u) = 2u;
    return (uint64_t)pin << 32;
}
uint32_t syscon_target_gpio_detach(uint32_t pin)
{
    if (pin >= SYSCON_GPIO_COUNT)
        gpio_assert(0x9bu, "pin < HAL_PLATFORM_PIN_NUM");
    volatile syscon_gpio_pin_t *descriptor =
        (volatile syscon_gpio_pin_t *)(uintptr_t)syscon_target_gpio_lookup((uint8_t)pin);
    uint32_t physical = descriptor->physical_pin;
    uint32_t mask = arm_lsl(1u, physical);
    syscon_gpio_handlers[pin].callback = 0;
    syscon_gpio_handlers[pin].context = 0;
    uint32_t port = descriptor->port;
    uint32_t old = U32(port + 0x1028u);
    U32(port + 0x1028u) = old & ~mask;
    return 0;
}
void syscon_target_gpio_irq(void)
{
    if (U32(0x40401130u) != 1u)
        return;
    uint32_t index = (U32(0x400a1020u) - 1u) & 255u;
    for (uint32_t pin = 0; pin != SYSCON_GPIO_COUNT; ++pin) {
        volatile syscon_gpio_pin_t *descriptor =
            (volatile syscon_gpio_pin_t *)(uintptr_t)syscon_target_gpio_lookup(pin);
        if (descriptor->port == 0x400a0000u && descriptor->physical_pin == index) {
            uint32_t callback = syscon_gpio_handlers[pin].callback;
            if (callback) {
                uint32_t context = syscon_gpio_handlers[pin].context;
                ((void (*)(uint32_t, uint32_t))(uintptr_t)callback)(pin, context);
            }
            return;
        }
    }
}
