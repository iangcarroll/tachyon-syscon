#include "application_state.h"
#include "logger_target.h"

volatile syscon_event_queue syscon_key_events __attribute__((section(".bss.syscon_key_events")));
volatile uint8_t syscon_key_event_buffer[SYSCON_KEY_QUEUE_CAPACITY]
    __attribute__((section(".bss.syscon_key_event_buffer")));
volatile uint8_t syscon_shutdown_pending __attribute__((section(".bss.syscon_shutdown_pending")));
volatile uint8_t syscon_key_started_off __attribute__((section(".bss.syscon_key_started_off")));
volatile uint8_t syscon_wakeup_pending __attribute__((section(".bss.syscon_wakeup_pending")));
uint8_t syscon_application_dso __attribute__((section(".bss.syscon_application_dso")));
volatile uint8_t syscon_console_buffer[SYSCON_PROTOCOL_CAPACITY]
    __attribute__((section(".bss.syscon_console_buffer")));
volatile syscon_protocol_context syscon_console_parser
    __attribute__((section(".data.syscon_console_parser"))) = {
        .port = 0,
        .buffer = (uint32_t)(uintptr_t)syscon_console_buffer,
        .echo = 1,
        .enabled = 1,
        .printer = (uint32_t)(uintptr_t)syscon_target_mfg_logger,
};
