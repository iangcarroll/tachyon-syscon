/* Physical-address reset/vector implementation. Offline experimental image. */
#include <stdint.h>
extern uint32_t __ram_exec_load[],__ram_exec_start[],__ram_exec_end[];
extern uint32_t __ram_extra_load[],__ram_extra_start[],__ram_extra_end[];
extern uint32_t __physical_initial_data[],__extra_bss_start[],__extra_bss_end[];
extern uint32_t __state_bss_start[],__state_bss_end[];
extern uint32_t __data_load[],__data_start[],__data_end[];
extern uint32_t __peripheral_data_load[],__peripheral_data_start[],__peripheral_data_end[];
extern uint32_t __peripheral_bss_start[],__peripheral_bss_end[];
extern uint32_t __irq_bss_start[],__irq_bss_end[];
extern uint32_t __power_data_load[],__power_data_start[],__power_data_end[];
extern uint32_t __power_bss_start[],__power_bss_end[];
extern void syscon_target_runtime_init(void);
extern void syscon_target_timestamp_constructor(void),syscon_target_queue_constructor(void);
extern void syscon_target_main(void),syscon_hardfault(void),syscon_nmi(void),syscon_default_exception(void);
extern void syscon_target_timer_tick(void),syscon_target_gpio_irq(void),syscon_target_i2c_irq(void);
extern void syscon_target_uart_irq(uint32_t);
void syscon_physical_uart0_irq(void){syscon_target_uart_irq(0x40108000u);}
void syscon_physical_uart1_irq(void){syscon_target_uart_irq(0x40100000u);}
static void copy(volatile uint32_t *to,const uint32_t *from,volatile uint32_t *end){while(to<end)*to++=*from++;}
_Noreturn void syscon_physical_reset(void){
    copy((uint32_t *)0x20000030u,__physical_initial_data,(uint32_t *)0x200002c0u);
    copy(__ram_exec_start,__ram_exec_load,__ram_exec_end);
    for(volatile uint32_t *p=(uint32_t *)0x200002c0u;p<(uint32_t *)0x20000820u;p++)*p=0;
    copy(__ram_extra_start,__ram_extra_load,__ram_extra_end);
    copy(__data_start,__data_load,__data_end);
    copy(__peripheral_data_start,__peripheral_data_load,__peripheral_data_end);
    copy(__power_data_start,__power_data_load,__power_data_end);
    for(volatile uint32_t *p=__power_bss_start;p<__power_bss_end;p++)*p=0;
    for(volatile uint32_t *p=__peripheral_bss_start;p<__peripheral_bss_end;p++)*p=0;
    for(volatile uint32_t *p=__irq_bss_start;p<__irq_bss_end;p++)*p=0;
    for(volatile uint32_t *p=__extra_bss_start;p<__extra_bss_end;p++)*p=0;
    for(volatile uint32_t *p=__state_bss_start;p<__state_bss_end;p++)*p=0;
    /* The original preinit list is empty and its init hook at7a50 returns. */
    syscon_target_runtime_init();
    syscon_target_main();syscon_hardfault();for(;;){}
}
typedef void (*vector_fn)(void);
__attribute__((section(".vectors"),used))
const vector_fn syscon_physical_vectors[48]={
 [0]=(vector_fn)0x20001000u,[1]=syscon_physical_reset,[2]=syscon_nmi,[3]=syscon_hardfault,
 [11]=syscon_default_exception,[14]=syscon_default_exception,[15]=syscon_target_timer_tick,
 [16]=syscon_default_exception,[17]=syscon_target_gpio_irq,[18]=syscon_default_exception,
 [20]=syscon_default_exception,[25]=syscon_default_exception,[29]=syscon_physical_uart1_irq,
 [31]=syscon_physical_uart0_irq,[32]=syscon_default_exception,[34]=syscon_default_exception,
 [36]=syscon_default_exception,[40]=syscon_target_i2c_irq,[41]=syscon_default_exception,[47]=syscon_default_exception
};
