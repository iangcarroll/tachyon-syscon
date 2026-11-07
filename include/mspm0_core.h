#ifndef SYSCON_MSPM0_CORE_H
#define SYSCON_MSPM0_CORE_H
#include <stdint.h>
#include "timers.h"

typedef void (*mspm0_dispatch)(void *,uint32_t function,uint32_t arg0,uint32_t arg1);
typedef struct {
    syscon_register_read read;
    syscon_register_write write;
    mspm0_dispatch dispatch;
    void *ctx;
} mspm0_environment;

void mspm0_reset_init(uint8_t ram[4096],const uint8_t *flash,const mspm0_environment *);
uint64_t mspm0_core_execute(uint8_t ram[4096],const mspm0_environment *,uint32_t entry,
    uint32_t pin,uint32_t arg1,uint32_t arg2,uint32_t arg3,const uint8_t *gpio_config);
#endif
