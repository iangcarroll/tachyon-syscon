#ifndef SYSCON_APPLICATION_TARGET_H
#define SYSCON_APPLICATION_TARGET_H
#include <stdint.h>
void syscon_target_runtime_init(void);
void syscon_target_timestamp_constructor(void);
void syscon_target_queue_constructor(void);
void syscon_target_queue_destructor(void *);
void syscon_target_queue_event(uint32_t);
uint32_t syscon_target_queue_count(uint32_t);
void syscon_target_request_off(void);
void syscon_target_diagnostic_write(uint32_t,uint32_t);
void syscon_target_parser_poll(void);
void syscon_target_wakeup_irq(uint32_t,uint32_t);
void syscon_target_wakeup_init(void);
void syscon_target_wakeup_enable(uint32_t);
void syscon_target_wakeup_poll(void);
void syscon_target_application_gpio_init(void);
void syscon_target_log_enable(uint32_t);
_Noreturn void syscon_target_main(void);
#endif
