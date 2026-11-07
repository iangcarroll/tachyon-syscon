/* ADC setup, raw conversion, voltage scaling and factory-calibrated temperature. */
#include "adc_target.h"
#include "adc_state.h"
#include "hal_helpers.h"
#include "mspm0_core_target.h"
#include "runtime_memory.h"
#include "runtime_arithmetic.h"

#define BYTE(address) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(address))
#define REGISTER(address) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(address))
#define STATE syscon_adc_state
#define ADC_BASE 0x40004000u
#define VREF_BASE 0x40030000u
#define FACTORY_ACCESS 0x40401300u
#define FACTORY_TEMPERATURE_CALIBRATION 0x41c4003cu
#define ADC_RESULT_ALIAS 0x556280u

enum {
    ADC_CLOCK_SOURCE = 1,
    ADC_CLOCK_FREQUENCY_RANGE = 5,
    ADC_CLOCK_DIVIDER_ENCODING = 2,
    REFERENCE_READY_ATTEMPTS = 100,
    REFERENCE_WAIT_CYCLES = 320,
    CONVERSION_CYCLES = 32000,
    SETTLE_CYCLES = 3200,
};

volatile syscon_adc_state_t syscon_adc_state
    __attribute__((section(".bss.syscon_adc_state")));
volatile uint8_t syscon_adc_vref_initialized
    __attribute__((section(".bss.syscon_adc_vref_initialized")));

extern void syscon_cycle_delay(uint32_t);

static void adc_assert(uint32_t original_line, const char *expression)
{
    /* Preserve the public diagnostic text and original line identifiers. */
    syscon_target_assert((uint32_t)(uintptr_t)"hal_adc.cpp", original_line,
                         (uint32_t)(uintptr_t)expression);
}

uint64_t syscon_target_adc_init(uint32_t pin, uint32_t config)
{
    volatile syscon_adc_channel_t *descriptor =
        (volatile syscon_adc_channel_t *)(uintptr_t)syscon_hal_adc_lookup((uint8_t)pin);
    if (!descriptor)
        adc_assert(21, "adc != nullptr");
    if (!config)
        adc_assert(22, "config != nullptr");

    uint32_t base = descriptor->peripheral;
    REGISTER(base + 0x804u) = 0xb1000003u;
    REGISTER(base + 0x800u) = 0x26000001u;
    uint32_t clock[2] = {
        ADC_CLOCK_SOURCE | (ADC_CLOCK_FREQUENCY_RANGE << 8),
        ADC_CLOCK_DIVIDER_ENCODING << 24,
    };
    syscon_hal_adc_clock(base, (uint32_t)(uintptr_t)clock);
    base = descriptor->peripheral;
    uint32_t old = REGISTER(base + 0x1104u);
    REGISTER(base + 0x1104u) = old ^ ((old ^ 0x100000u) & 0x130001u);
    old = REGISTER(base + 0x1108u);
    REGISTER(base + 0x1108u) = old & 0xe0e0fff8u;
    REGISTER(base + 0x1114u) = 0x1au;
    old = REGISTER(base + 0x1100u);
    REGISTER(base + 0x1100u) = old | 0x10000u;

    syscon_rt_memcpy((void *)STATE.configuration, (const void *)(uintptr_t)config,
                    sizeof(STATE.configuration));
    /* Read the caller again after copying. It may alias the retained buffer. */
    uint32_t high = BYTE(config + 5u);
    uint32_t low = BYTE(config + 4u);
    STATE.scale_le[1] = (uint8_t)high;
    STATE.scale_le[0] = (uint8_t)low;
    STATE.scale_le[2] = 0;
    STATE.scale_le[3] = 0;
    return (uint64_t)clock[0] << 32;
}

uint32_t syscon_target_adc_temperature(void)
{
    if (!syscon_adc_vref_initialized) {
        REGISTER(VREF_BASE + 0x804u) = 0xb1000001u;
        REGISTER(VREF_BASE + 0x800u) = 0x26000001u;
        uint8_t clock[2] = {8, 0};
        syscon_hal_vref_clock(VREF_BASE, (uint32_t)(uintptr_t)clock);
        union { uint32_t words[3]; uint16_t halves[6]; } configuration;
        syscon_rt_memset(&configuration, 0, sizeof(configuration));
        configuration.halves[0] = 0x8001u;
        syscon_hal_vref_config(VREF_BASE, (uint32_t)(uintptr_t)&configuration);
        syscon_adc_vref_initialized = 1;
    }

    uint32_t remaining = REFERENCE_READY_ATTEMPTS;
    do {
        if (REGISTER(VREF_BASE + 0x1104u) & 1u)
            break;
        --remaining;
        syscon_cycle_delay(REFERENCE_WAIT_CYCLES);
    } while (remaining);
    /* This final read is intentional: READY may change after the loop check. */
    if (!(REGISTER(VREF_BASE + 0x1104u) & 1u))
        return 0x80000000u;

    uint32_t old = REGISTER(ADC_BASE + 0x1100u);
    REGISTER(ADC_BASE + 0x1100u) = old & ~1u;
    REGISTER(ADC_BASE + 0x1180u) = 0x100020bu;
    old = REGISTER(ADC_BASE + 0x1100u);
    REGISTER(ADC_BASE + 0x1100u) = old | 1u;
    old = REGISTER(ADC_BASE + 0x1104u);
    REGISTER(ADC_BASE + 0x1104u) = old | 0x100u;
    syscon_cycle_delay(CONVERSION_CYCLES);
    old = REGISTER(ADC_BASE + 0x1104u);
    REGISTER(ADC_BASE + 0x1104u) = old & ~0x100u;
    syscon_cycle_delay(SETTLE_CYCLES);

    uint32_t measured = REGISTER(ADC_BASE + ADC_RESULT_ALIAS) & 0xffffu;
    uint32_t access = REGISTER(FACTORY_ACCESS) & 7u;
    REGISTER(FACTORY_ACCESS) = 5;
    uint32_t calibration = REGISTER(FACTORY_TEMPERATURE_CALIBRATION);
    REGISTER(FACTORY_ACCESS) = access;
    if (!calibration || calibration == 0xfffu)
        return 0x80000000u;

    /* Deliberate 32-bit wrapping subtraction/product, then signed division.
     * The result is in tenths of a degree C, referenced to 30 degrees C. */
    uint32_t product = (measured - calibration) * 14000u;
    return (uint32_t)syscon_rt_idiv32(product, (uint32_t)-7168) + 300u;
}

uint32_t syscon_target_adc_raw(uint32_t pin)
{
    volatile syscon_adc_channel_t *descriptor =
        (volatile syscon_adc_channel_t *)(uintptr_t)syscon_hal_adc_lookup((uint8_t)pin);
    if (!descriptor)
        adc_assert(131, "adc != nullptr");
    uint32_t base = descriptor->peripheral;
    uint32_t old = REGISTER(base + 0x1100u);
    REGISTER(base + 0x1100u) = old & ~1u;
    uint32_t channel = descriptor->channel;
    uint32_t slot = descriptor->result_slot;
    REGISTER(base + 0x1180u + slot * 4u) = channel | 0x1000000u;
    old = REGISTER(base + 0x1100u);
    REGISTER(base + 0x1100u) = old | 1u;
    old = REGISTER(base + 0x1104u);
    REGISTER(base + 0x1104u) = old | 0x100u;
    syscon_cycle_delay(CONVERSION_CYCLES);
    /* A delay can expose descriptor changes. Reload both base and slot. */
    base = descriptor->peripheral;
    old = REGISTER(base + 0x1104u);
    REGISTER(base + 0x1104u) = old & ~0x100u;
    syscon_cycle_delay(SETTLE_CYCLES);
    slot = descriptor->result_slot;
    base = descriptor->peripheral;
    return REGISTER(base + ADC_RESULT_ALIAS + slot * 4u) & 0xffffu;
}

uint32_t syscon_target_adc_millivolts(uint32_t pin)
{
    uint32_t raw = syscon_target_adc_raw(pin);
    if (raw & 0x80000000u)
        return raw;
    /* Keep byte access order, including the high byte read before the low. */
    uint32_t high = STATE.scale_le[1];
    uint32_t low = STATE.scale_le[0];
    uint32_t third = STATE.scale_le[2];
    uint32_t fourth = STATE.scale_le[3];
    uint32_t product = raw * (low | (high << 8) | (third << 16) | (fourth << 24));
    /* Signed division by 4096 toward zero without implementation-defined
     * signed shifts or overflow. */
    uint32_t rounded = product + ((product & 0x80000000u) ? 4095u : 0u);
    return (rounded >> 12) | ((rounded & 0x80000000u) ? 0xfff00000u : 0u);
}
