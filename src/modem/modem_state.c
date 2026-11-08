#include "modem_state.h"
#include "logger_target.h"

volatile syscon_modem_boot_state syscon_modem_boot
    __attribute__((section(".bss.syscon_modem_boot")));
volatile syscon_modem_timing_state syscon_modem_timing
    __attribute__((section(".bss.syscon_modem_timing")));
volatile syscon_modem_runtime_state syscon_modem_runtime
    __attribute__((section(".bss.syscon_modem_runtime")));
volatile uint8_t syscon_modem_buffer[SYSCON_PROTOCOL_CAPACITY]
    __attribute__((section(".bss.syscon_modem_buffer")));
uint8_t syscon_modem_scratch[SYSCON_PROTOCOL_CAPACITY]
    __attribute__((section(".bss.syscon_modem_scratch")));
volatile syscon_protocol_context syscon_modem_parser
    __attribute__((section(".data.syscon_modem_parser"))) = {
        .port = 1,
        .buffer = (uint32_t)(uintptr_t)syscon_modem_buffer,
        .enabled = 1,
        .printer = (uint32_t)(uintptr_t)syscon_target_sg560d_printf,
};
/* Milliseconds indexed by the public shutdown reason (including brownout). */
const uint32_t syscon_modem_retry_delays[7] = {30000, 900000, 900000, 5000, 120000, 120000, 10000};

const char syscon_modem_fct_label[] = "FCT";
const char syscon_modem_fastboot_label[] = "FASTBOOT";
