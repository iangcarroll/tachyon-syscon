#include "format_core_target.h"
#include "format.h"
#include "runtime_arithmetic.h"
_Static_assert(sizeof(void *)==4,"Target ARM32 pointers required");
uint64_t syscon_target_format_digits(uint64_t value,uint32_t buffer,uint32_t radix,uint32_t alphabet_offset){
    uint32_t count=0;uint8_t alphabet=(uint8_t)(alphabet_offset+55);
    for(;;){
        uint64_t old=value,remainder;
        /* The original calls the EABI division wrapper, whose zero-divisor
         * branch returns quotient0/max and leaves zero in remainder R2/R3.
         * The raw udiv64 algorithm has a different zero-divisor contract. */
        if(!radix){value=value?UINT64_MAX:0;remainder=0;}
        else value=syscon_rt_udiv64(value,radix,&remainder);
        uint32_t digit=(uint32_t)remainder;
        uint32_t base=(int32_t)digit>9?alphabet:'0';
        *(volatile uint8_t *)(uintptr_t)(buffer+count)=(uint8_t)(base+digit);++count;
        if(!(old>>32) && radix>(uint32_t)old)break;
    }
    return ((uint64_t)buffer<<32)|count;
}
uint32_t syscon_target_format_forward(uint32_t character,uint32_t context){
    volatile uint32_t *out=(volatile uint32_t *)(uintptr_t)context;
    out[2]=out[2]+1;
    uint32_t callback=out[0],argument=out[1];
    return ((uint32_t (*)(uint32_t,uint32_t))(uintptr_t)callback)(character,argument);
}
static void invoke(void *ignored,uint32_t callback,uint32_t character,uint32_t context){
    (void)ignored;
    (void)((uint32_t (*)(uint32_t,uint32_t))(uintptr_t)callback)(character,context);
}
uint32_t syscon_target_vformat_callback(uint32_t callback,uint32_t context,uint32_t format,uint32_t arguments){
    return syscon_vformat_callback(callback,context,invoke,0,format,arguments,0).length;
}
