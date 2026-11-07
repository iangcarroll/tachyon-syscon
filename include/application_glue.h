#ifndef SYSCON_APPLICATION_GLUE_H
#define SYSCON_APPLICATION_GLUE_H
#include "syscon.h"
#include "mspm0_core.h"
#include "uart.h"
int syscon_configuration_init(syscon_store *,syscon_store *,uint8_t runtime[22]);
void syscon_app_gpio_init(uint8_t ram[4096],const mspm0_environment *);
void syscon_uart_vector(syscon_uart *,uint32_t,const syscon_uart_io *);
void syscon_log_enable(uint8_t ram[4096],uint32_t);
int syscon_default_action(void);
void syscon_sg560d_direct(syscon_uart *,const uint8_t *,uint32_t,const syscon_uart_io *);
#endif
