/* Original-ABI core/GPIO reconstruction. Fixed addresses are original image ABI,
 * including its read-only strings/tables; this is not a relocatable board image. */
#include "mspm0_core_target.h"
#include "runtime_memory.h"
#define U8(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))

static uint32_t arm_lsl(uint32_t value, uint32_t shift) {
    shift &= 255u;
    return shift < 32u ? value << shift : 0;
}
static void gpio_assert(uint32_t line, uint32_t expression) {
    uint32_t file = 0xdf49u;
    if (syscon_rt_strrchr((const void *)(uintptr_t)file, '/'))
        file = (uint32_t)(uintptr_t)syscon_rt_strrchr((const void *)(uintptr_t)file, '/') + 1u;
    syscon_target_assert(file, line, expression);
}
uint32_t syscon_target_watchdog_init(void) {
    U32(0x40080804u)=0xb1000003u;
    U32(0x40080800u)=0x26000001u;
    U32(0x40081104u)=0xbe000000u;
    U32(0x40081100u)=0xc9020033u;
    U32(0x40081108u)=0xa7u;
    return 0;
}
uint32_t syscon_target_watchdog_feed(void) { U32(0x40081108u)=0xa7u; return 0; }
void syscon_target_hal_noop(void) {}
uint32_t syscon_target_gpio_lookup(uint32_t pin) {
    return pin < 25u ? 0x2000016cu + pin*8u : 0;
}
uint32_t syscon_target_reset_cause(void) {
    uint32_t cause=U8(0x20000254u);
    if (cause==255u) {
        cause=U32(0x400b0220u)&31u;
        U8(0x20000254u)=(uint8_t)cause;
    }
    uint32_t index=(cause-1u)&255u;
    return index < 21u ? U8(0xdeb2u+index) : 3u;
}
uint32_t syscon_target_reset_cause_name(uint32_t cause) {
    return cause < 7u ? U32(0xdec8u+cause*4u) : 0xccebu;
}
uint32_t syscon_target_gpio_config(uint32_t pin,uint32_t config) {
    if (!config) gpio_assert(0x21u,0xdf37u);
    if (pin>=25u) gpio_assert(0x22u,0xdf8eu);
    uint32_t descriptor=syscon_target_gpio_lookup((uint8_t)pin);
    uint32_t physical=U8(descriptor+4u);
    uint32_t mask=arm_lsl(1u,physical);
    uint32_t port=U32(descriptor);
    U32(port+0x800u)=0x26000001u;
    uint32_t mode=U8(config+4u);
    if (!mode) {
        U32(port+0x12e0u)=mask;
        uint32_t mux=U8(descriptor+5u);
        uint32_t pull=U8(config+5u);
        uint32_t address=0x40428004u+mux*4u;
        if (pull==1u) U32(address)=0xe0081u;
        else if (pull==2u) U32(address)=0xd0081u;
        else {
            U32(address)=0x40081u;
            uint32_t old=U32(address);
            U32(address)=old|0x2000000u;
        }
    } else if (mode==1u) {
        uint32_t mux=U8(descriptor+5u);
        U32(0x40428004u+mux*4u)=0x81u;
        uint32_t flags=U32(config+8u);
        if (flags&2u) {
            uint32_t value=U8(config+7u);
            U32(port+(value ? 0x1290u : 0x12a0u))=mask;
        }
        U32(port+0x12d0u)=mask;
    }
    return 0;
}
uint32_t syscon_target_gpio_write(uint32_t pin,uint32_t value) {
    if (pin>=25u) gpio_assert(0x61u,0xdf8eu);
    uint32_t descriptor=syscon_target_gpio_lookup((uint8_t)pin);
    uint32_t physical=U8(descriptor+4u);
    uint32_t mask=arm_lsl(1u,physical);
    uint32_t port=U32(descriptor);
    U32(port+(value ? 0x1290u : 0x12a0u))=mask;
    return 0;
}
uint32_t syscon_target_gpio_toggle(uint32_t pin) {
    if (pin>=25u) gpio_assert(0x6du,0xdf8eu);
    uint32_t descriptor=syscon_target_gpio_lookup((uint8_t)pin);
    uint32_t physical=U8(descriptor+4u);
    uint32_t port=U32(descriptor);
    U32(port+0x12b0u)=arm_lsl(1u,physical);
    return 0;
}
uint32_t syscon_target_gpio_read(uint32_t pin) {
    if (pin>=25u) gpio_assert(0x74u,0xdf8eu);
    uint32_t descriptor=syscon_target_gpio_lookup((uint8_t)pin);
    uint32_t port=U32(descriptor);
    uint32_t input=U32(port+0x1380u);
    uint32_t physical=U8(descriptor+4u);
    return (input & arm_lsl(1u,physical)) != 0;
}
uint64_t syscon_target_gpio_attach(uint32_t pin,uint32_t edge,uint32_t callback,uint32_t context) {
    if (pin>=25u) gpio_assert(0x7au,0xdf8eu);
    uint32_t descriptor=syscon_target_gpio_lookup((uint8_t)pin);
    uint32_t physical=U8(descriptor+4u);
    U32(0x20000698u+pin*8u)=callback;
    uint32_t mask=arm_lsl(1u,physical);
    U32(0x2000069cu+pin*8u)=context;
    if (edge!=1u && edge!=2u) edge=3u;
    uint32_t port=U32(descriptor);
    uint32_t reg=port+(physical<16u ? 0x1390u : 0x13a0u);
    uint32_t shift=(physical<16u ? physical : physical-16u)*2u;
    uint32_t field=arm_lsl(3u,shift);
    uint32_t selected=arm_lsl(edge,shift);
    uint32_t old=U32(reg);
    U32(reg)=old&~field;
    old=U32(reg);
    U32(reg)=old|selected;
    old=U32(port+0x1048u);
    U32(port+0x1048u)=old|mask;
    old=U32(port+0x1028u);
    U32(port+0x1028u)=old|mask;
    U32(0xe000e100u)=2u;
    return (uint64_t)pin<<32;
}
uint32_t syscon_target_gpio_detach(uint32_t pin) {
    if (pin>=25u) gpio_assert(0x9bu,0xdf8eu);
    uint32_t descriptor=syscon_target_gpio_lookup((uint8_t)pin);
    uint32_t physical=U8(descriptor+4u);
    uint32_t mask=arm_lsl(1u,physical);
    U32(0x20000698u+pin*8u)=0;
    U32(0x2000069cu+pin*8u)=0;
    uint32_t port=U32(descriptor);
    uint32_t old=U32(port+0x1028u);
    U32(port+0x1028u)=old&~mask;
    return 0;
}
void syscon_target_gpio_irq(void) {
    if (U32(0x40401130u)!=1u) return;
    uint32_t index=(U32(0x400a1020u)-1u)&255u;
    for (uint32_t pin=0;pin!=25u;++pin) {
        uint32_t descriptor=syscon_target_gpio_lookup(pin);
        if (U32(descriptor)==0x400a0000u && U8(descriptor+4u)==index) {
            uint32_t callback=U32(0x20000698u+pin*8u);
            if (callback) {
                uint32_t context=U32(0x2000069cu+pin*8u);
                ((void (*)(uint32_t,uint32_t))(uintptr_t)callback)(pin,context);
            }
            return;
        }
    }
}
