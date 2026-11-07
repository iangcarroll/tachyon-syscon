#include "scheduling_target.h"
#include "runtime_memory.h"
#include "scheduling_state.h"
volatile syscon_retained syscon_retained_state __attribute__((section(".bss.syscon_retained_state")));
#define STATE syscon_retained_state
#define SCRATCH ((volatile uint32_t *)(uintptr_t)0x400b0400)
void syscon_target_retained_commit(void) {
    uint8_t copy[3];syscon_rt_memcpy(copy,(const void *)&STATE,3);
    SCRATCH[0]=copy[0];SCRATCH[1]=copy[1];SCRATCH[2]=copy[2];
}
void syscon_target_retained_load(void) {
    uint32_t magic=SCRATCH[0],modes=SCRATCH[1],boots=SCRATCH[2];
    uint8_t copy[3]={(uint8_t)magic,(uint8_t)modes,(uint8_t)boots};
    syscon_rt_memcpy((void *)&STATE,copy,3);
    syscon_target_logger(3,(const char *)0xcdcd,(const char *)0xcdab,(uint8_t)magic,(uint8_t)modes,(uint8_t)boots);
    uint8_t observed=STATE.magic;
    if(observed!=0x5b){
        syscon_target_logger(1,(const char *)0xcdcd,(const char *)0xcdd2,observed,0x5b);
        syscon_rt_memset((void *)&STATE,0,3);STATE.magic=0x5b;
        syscon_target_retained_commit();
    }
}
void syscon_target_retained_clear_registers(void){SCRATCH[0]=0;SCRATCH[1]=0;SCRATCH[2]=0;}
void syscon_target_retained_set_modem(uint32_t value){STATE.modes=(STATE.modes&0xf0)|(value&15);syscon_target_retained_commit();}
uint32_t syscon_target_retained_modem(void){return STATE.modes&15;}
void syscon_target_retained_set_battery(uint32_t value){STATE.modes=(STATE.modes&15)|(value<<4);syscon_target_retained_commit();}
uint32_t syscon_target_retained_battery(void){return STATE.modes>>4;}
void syscon_target_retained_increment_boots(void){uint8_t boots=STATE.boots;if(boots!=255)STATE.boots=boots+1;syscon_target_retained_commit();}
uint32_t syscon_target_retained_boots(void){return STATE.boots;}
