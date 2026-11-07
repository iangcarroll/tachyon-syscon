/* Fixed-layout RGB state machine with original MMIO-facing dependencies. */
#include "rgb_target.h"
#include "runtime_memory.h"
#include "scheduling_target.h"
#include "pwm_target.h"
#include <stdint.h>
#define B(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define H(a) (*(volatile uint16_t *)(uintptr_t)(uint32_t)(a))
#define W(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))
#define R 0x200003a8u


static float decode(uint32_t bits){union{uint32_t u;float f;}v={.u=bits};return v.f;}
static uint32_t encode(float value){union{float f;uint32_t u;}v={.f=value};return v.u;}
extern uint32_t syscon_rt_f2u(uint32_t bits);
/* Explicit bit helper avoids an undefined out-of-range C float cast. */
uint32_t syscon_target_rgb_scale(uint32_t channel){
    uint8_t level=(uint8_t)syscon_rt_f2u(W(R+8));
    uint8_t value=(uint8_t)((channel*(uint32_t)level)/100u);
    if(!B(R+16))value=(uint8_t)~value;
    return value;
}
void syscon_target_rgb_flush(void){
    uint32_t value=syscon_target_rgb_scale(B(R+1));syscon_target_pwm_write(3,value);
    value=syscon_target_rgb_scale(B(R+2));syscon_target_pwm_write(2,value);
    value=syscon_target_rgb_scale(B(R+3));syscon_target_pwm_write(1,value);
}
int syscon_target_rgb_init(uint32_t active_high){
    syscon_target_pwm_init(3);syscon_target_pwm_init(2);syscon_target_pwm_init(1);
    syscon_rt_memset((void *)R,0,20);B(R+16)=(uint8_t)active_high;
    int result=syscon_target_timer_register(20,0,(uint32_t)(uintptr_t)syscon_target_rgb_tick,0);
    if(result<0)syscon_target_logger(1,(const char *)0xce50,(const char *)0xce05,result);
    syscon_target_timer_init();return 0;
}
int syscon_target_rgb_brightness(uint32_t brightness,uint32_t flush){
    if(brightness>100)brightness=100;
    B(R+4)=(uint8_t)brightness;W(R+8)=encode((float)brightness);
    if(flush)syscon_target_rgb_flush();
    return 0;
}
int syscon_target_rgb_pattern(uint32_t pattern,uint32_t flush){
    if(B(R)!=pattern){
        B(R)=(uint8_t)pattern;
        if(pattern==1)B(R+12)=0;
        else if(pattern==2)H(R+14)=500;
        else if(pattern==3)H(R+14)=100;
        B(R+13)=0;
    }
    if(flush)syscon_target_rgb_flush();
    return 0;
}
int syscon_target_rgb_configure(uint32_t config){
    if(!config)return -1;
    uint32_t green=B(config+1),blue=B(config+2),red=B(config);
    B(R+2)=(uint8_t)green;B(R+1)=(uint8_t)red;B(R+3)=(uint8_t)blue;
    syscon_target_rgb_brightness(B(config+3),0);
    return syscon_target_rgb_pattern(B(config+4),1);
}
int syscon_target_rgb_preset(uint32_t preset,uint32_t duration){
    if(preset>=10)return -1;
    uint32_t previous=B(R+21);B(R+21)=(uint8_t)preset;B(R+22)=(uint8_t)previous;
    W(R+24)=duration/20;return syscon_target_rgb_configure(0xcf18+preset*5);
}
uint64_t syscon_target_rgb_tick(uint32_t arg,uint32_t seed){
    uint32_t duration=W(R+24);
    if(duration){--duration;W(R+24)=duration;if(!duration)syscon_target_rgb_preset(B(R+22),0);}
    uint32_t pattern=B(R);
    if(pattern==1){
        uint32_t brightness=B(R+4);float target=(float)(int32_t)brightness;
        seed=encode(target);float step=target/100.0f;
        uint32_t increasing=B(R+12);float level=decode(W(R+8));
        if(!increasing){
            if(level<=step){W(R+8)=0;B(R+12)=(uint8_t)pattern;}
            else W(R+8)=encode(decode(W(R+8))-step);
        }else{
            W(R+8)=encode(level+step);
            if(target<=decode(W(R+8))){W(R+8)=encode((float)brightness);B(R+12)=0;}
        }
    }else if(pattern-2u<2){
        B(R+13)=(uint8_t)(B(R+13)+1u);
        uint32_t elapsed=B(R+13)*20u,interval=H(R+14);
        if(elapsed<interval)return ((uint64_t)seed<<32)|arg;
        B(R+13)=0;
        if(decode(W(R+8))==0.0f)W(R+8)=encode((float)B(R+4));else W(R+8)=0;
    }else if(pattern==5){
        B(R+13)=(uint8_t)(B(R+13)+1u);
        if(B(R+13)<3)return ((uint64_t)seed<<32)|arg;
        B(R+13)=0;uint32_t next=(uint8_t)(B(R+20)+1u);B(R+20)=(uint8_t)(next<10?next:0);
        uint32_t pointer=0xcf4a+B(R+20)*3u;
        uint32_t green=B(pointer+1),red=B(pointer),blue=B(pointer+2);
        B(R+1)=(uint8_t)red;B(R+2)=(uint8_t)green;B(R+3)=(uint8_t)blue;
    }else return ((uint64_t)seed<<32)|arg;
    syscon_target_rgb_flush();return ((uint64_t)seed<<32)|arg;
}
uint32_t syscon_target_rgb_state(void){return B(R+21);}
uint32_t syscon_target_rgb_get_config(uint32_t out){
    if(!out)return 0;
    B(out)=B(R+21);B(out+1)=B(R+1);B(out+2)=B(R+2);
    B(out+3)=B(R+3);B(out+4)=B(R+4);B(out+5)=B(R);return 1;
}
uint32_t syscon_target_rgb_state_name(uint32_t state){return state<10?W(0xced8+state*4):0xce55;}
uint32_t syscon_target_rgb_pattern_name(uint32_t pattern){return pattern<6?W(0xcf00+pattern*4):0xce55;}
void syscon_target_rgb_key_feedback(void){syscon_target_rgb_preset(9,40);}
