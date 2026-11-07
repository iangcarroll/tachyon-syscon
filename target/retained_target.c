#include "scheduling_target.h"
#include "runtime_memory.h"
#define R ((volatile uint8_t *)(uintptr_t)0x200000da)
#define SCRATCH ((volatile uint32_t *)(uintptr_t)0x400b0400)
void syscon_target_retained_commit(void) {
    uint8_t copy[3];syscon_rt_memcpy(copy,(const void *)R,3);
    SCRATCH[0]=copy[0];SCRATCH[1]=copy[1];SCRATCH[2]=copy[2];
}
void syscon_target_retained_load(void) {
    uint32_t magic=SCRATCH[0],modes=SCRATCH[1],boots=SCRATCH[2];
    uint8_t copy[3]={(uint8_t)magic,(uint8_t)modes,(uint8_t)boots};
    syscon_rt_memcpy((void *)R,copy,3);
    syscon_target_logger(3,(const char *)0xcdcd,(const char *)0xcdab,(uint8_t)magic,(uint8_t)modes,(uint8_t)boots);
    uint8_t observed=R[0];
    if(observed!=0x5b){
        syscon_target_logger(1,(const char *)0xcdcd,(const char *)0xcdd2,observed,0x5b);
        syscon_rt_memset((void *)R,0,3);R[0]=0x5b;
        syscon_target_retained_commit();
    }
}
void syscon_target_retained_clear_registers(void){SCRATCH[0]=0;SCRATCH[1]=0;SCRATCH[2]=0;}
void syscon_target_retained_set_modem(uint32_t value){R[1]=(R[1]&0xf0)|(value&15);syscon_target_retained_commit();}
uint32_t syscon_target_retained_modem(void){return R[1]&15;}
void syscon_target_retained_set_battery(uint32_t value){R[1]=(R[1]&15)|(value<<4);syscon_target_retained_commit();}
uint32_t syscon_target_retained_battery(void){return R[1]>>4;}
void syscon_target_retained_increment_boots(void){uint8_t boots=R[2];if(boots!=255)R[2]=boots+1;syscon_target_retained_commit();}
uint32_t syscon_target_retained_boots(void){return R[2];}
