/* Reconstructed from the pinned original Thumb bodies; no DriverLib linkage. */
#include "hal_helpers.h"
#define U8(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define U16(a) (*(volatile uint16_t *)(uintptr_t)(uint32_t)(a))
#define U32(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))

uint32_t syscon_hal_adc_lookup(uint32_t id) {
    for (uint32_t i = 0; i != 6; ++i)
        if ((uint32_t)U8(0x200000f4u + 12u*i) == id)
            return 0x200000f4u + 12u*i;
    return 0;
}
uint32_t syscon_hal_pwm_lookup(uint32_t id) {
    if ((uint32_t)U8(0x20000148u) == id) return 0x20000148u;
    if ((uint32_t)U8(0x20000154u) == id) return 0x20000154u;
    if ((uint32_t)U8(0x20000160u) == id) return 0x20000160u;
    return 0;
}
uint32_t syscon_hal_uart_lookup(uint32_t index) {
    return index < 2u ? 0x20000234u + index*16u : 0;
}
uint32_t syscon_hal_i2c_lookup(uint32_t index) {
    return index == 0 ? 0x2000013cu : 0;
}
void syscon_hal_adc_clock(uint32_t base, uint32_t config) {
    uint32_t source = U8(config);
    uint32_t old = U32(base + 0x808u);
    U32(base + 0x808u) = old ^ ((old ^ (source | 0xa9000000u)) & 0xff000003u);
    old = U32(base + 0x1100u);
    uint32_t divider = U32(config + 4u);
    U32(base + 0x1100u) = old ^ ((old ^ divider) & 0x07000000u);
    uint32_t frequency = U8(config + 1u);
    U32(base + 0x1110u) = frequency;
}
void syscon_hal_i2c_clock(uint32_t base, uint32_t config) {
    uint32_t source = U8(config);
    uint32_t old = U32(base + 0x1004u);
    U32(base + 0x1004u) = old ^ ((old ^ source) & 12u);
    uint32_t divider = U8(config + 1u);
    old = U32(base + 0x1000u);
    U32(base + 0x1000u) = old ^ ((old ^ divider) & 7u);
}
void syscon_hal_i2c_fill_tx(uint32_t base, uint32_t data, uint32_t count) {
    uint32_t i = 0;
    /* Only the comparison truncates. The data index remains 32-bit, including
     * after 65535. A count above 65535 cannot terminate by count comparison. */
    while ((uint32_t)(uint16_t)i < count) {
        if ((U32(base + 0x123cu) & 0xf00u) == 0) return;
        uint32_t byte = U8(data + i);
        ++i;
        U32(base + 0x1220u) = byte;
    }
}
void syscon_hal_i2c_flush_tx(uint32_t base) {
    uint32_t control = U32(base + 0x1238u);
    U32(base + 0x1238u) = control | 0x80u;
    while ((U32(base + 0x123cu) & 0xf00u) != 0x800u) {}
    control = U32(base + 0x1238u);
    U32(base + 0x1238u) = control & ~0x80u;
}
void syscon_hal_i2c_flush_rx(uint32_t base) {
    uint32_t control = U32(base + 0x1238u);
    U32(base + 0x1238u) = control | 0x8000u;
    while ((U32(base + 0x123cu) & 15u) != 0) {}
    control = U32(base + 0x1238u);
    U32(base + 0x1238u) = control & ~0x8000u;
}
void syscon_hal_uart_put_blocking(uint32_t base, uint32_t value) {
    while (U32(base + 0x1108u) & 0x80u) {}
    U32(base + 0x1120u) = value;
}
void syscon_hal_vref_config(uint32_t base, uint32_t config) {
    uint32_t byte1 = U8(config + 1u);
    uint32_t byte0 = U8(config);
    uint32_t half2 = U16(config + 2u);
    U32(base + 0x1100u) = byte0 | byte1 | half2;
    uint32_t word8 = U32(config + 8u);
    uint32_t word4 = U32(config + 4u);
    U32(base + 0x1108u) = (word8 << 16) | word4;
}
void syscon_hal_vref_clock(uint32_t base, uint32_t config) {
    uint32_t source = U8(config);
    U32(base + 0x1008u) = source;
    uint32_t divider = U8(config + 1u);
    U32(base + 0x1000u) = divider;
}
