#ifndef SYSCON_ADC_STATE_H
#define SYSCON_ADC_STATE_H
#include <stdint.h>

/* Board logical pin -> ADC peripheral, channel and result slot. This is mutable
 * because the original reloads descriptors across conversion delays. */
typedef struct {
    uint8_t pin;
    uint8_t reserved[3];
    uint32_t peripheral;
    uint8_t channel;
    uint8_t result_slot;
    uint8_t trailing_reserved[2];
} syscon_adc_channel_t;
extern volatile syscon_adc_channel_t syscon_adc_channels[6];

typedef struct {
    /* The original retains all seven caller bytes, then rereads the scale from
     * that caller buffer. Overlap must retain forward-byte-copy semantics. */
    uint8_t configuration[7];
    uint8_t scale_le[4];
} syscon_adc_state_t;
extern volatile syscon_adc_state_t syscon_adc_state;
extern volatile uint8_t syscon_adc_vref_initialized;
#endif
