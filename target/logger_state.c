#include "logger_state.h"
volatile uint8_t syscon_log_enabled __attribute__((section(".bss.syscon_log_enabled")));
const char syscon_log_mfg_tag[] = "MFGD";
