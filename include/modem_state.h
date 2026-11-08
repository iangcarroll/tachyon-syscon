#ifndef SYSCON_MODEM_STATE_H
#define SYSCON_MODEM_STATE_H
#include <stdint.h>
#include "protocol_state.h"

/* Two volatile words preserve the MCU's original low/high access order. */
typedef struct {
    uint32_t low, high;
} syscon_modem_timestamp;
typedef struct {
    uint8_t mode, reserved[3];
    const char *label;
    uint8_t rgb[3], restarting;
} syscon_modem_boot_state;
typedef struct {
    uint8_t mode, reserved[3];
    uint32_t special_started;
    syscon_modem_timestamp wake_deadline;
} syscon_modem_timing_state;
typedef struct {
    syscon_modem_timestamp started, battery_restore_deadline;
    uint8_t usb_present, current_state, expected_state, reserved;
    uint32_t retry_count;
    uint8_t temporary_dcdc, rgb_history[3];
    uint32_t reserved_word;
    syscon_modem_timestamp retry_deadline;
    uint8_t retry_active, usb_debouncing, initialized, padding[5];
    syscon_modem_timestamp wake_warning_deadline, transition_deadline, usb_rise;
    uint8_t retry_reason, padding_reason[3];
    uint32_t green_changed, rgb_changed;
} syscon_modem_runtime_state;
_Static_assert(sizeof(syscon_modem_boot_state) == 12, "Modem boot state");
_Static_assert(sizeof(syscon_modem_timing_state) == 16, "Modem timing state");
_Static_assert(sizeof(syscon_modem_runtime_state) == 84, "Modem runtime state");
extern volatile syscon_modem_boot_state syscon_modem_boot;
extern volatile syscon_modem_timing_state syscon_modem_timing;
extern volatile syscon_modem_runtime_state syscon_modem_runtime;
extern volatile syscon_protocol_context syscon_modem_parser;
extern volatile uint8_t syscon_modem_buffer[SYSCON_PROTOCOL_CAPACITY];
extern uint8_t syscon_modem_scratch[SYSCON_PROTOCOL_CAPACITY];
extern const char syscon_modem_fct_label[], syscon_modem_fastboot_label[];
extern const uint32_t syscon_modem_retry_delays[7];
#endif
