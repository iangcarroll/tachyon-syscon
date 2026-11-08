#include "application_glue.h"
int syscon_configuration_init(syscon_store *identity,syscon_store *config,uint8_t runtime[22]) {
    if(syscon_store_init(identity)<0)return -1;
    if(syscon_store_init(config)<0)return -1;
    syscon_config_load(config,identity,runtime);
    return 0;
}
void syscon_app_gpio_init(uint8_t ram[4096],const mspm0_environment *env) {
    const uint8_t config[12]={0,0,0,0,0,2,0,0,0,0,0,0};
    mspm0_core_execute(ram,env,0x7f58,10,0,0,0,config);
    mspm0_core_execute(ram,env,0x7f58,9,0,0,0,config);
    mspm0_core_execute(ram,env,0x7f58,24,0,0,0,config);
}
void syscon_uart_vector(syscon_uart *uart,uint32_t vector,const syscon_uart_io *io) {
    if(vector==0x8e6c)syscon_uart_irq(uart,0x40108000,io);
    else if(vector==0x8e7c)syscon_uart_irq(uart,0x40100000,io);
}
void syscon_log_enable(uint8_t ram[4096],uint32_t value) {ram[0x80c]=(uint8_t)value;}
int syscon_default_action(void) {return -1;}
void syscon_sg560d_direct(syscon_uart *uart,const uint8_t *data,uint32_t size,const syscon_uart_io *io) {
    syscon_uart_write_buffer(uart,1,data,size,io);
}
