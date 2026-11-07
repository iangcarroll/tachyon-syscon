/* Complete original UART parser with target callbacks and packed descriptors. */
#include "protocol_target.h"
#include "runtime_memory.h"
#include "runtime_scan.h"
#include "runtime_support.h"
#include "uart_ring_target.h"
#include "callback_helpers.h"
#include "logger_target.h"
#include <stdint.h>
#define B(a) (*(volatile uint8_t *)(uintptr_t)(uint32_t)(a))
#define W(a) (*(volatile uint32_t *)(uintptr_t)(uint32_t)(a))
#define S(a) ((const char *)(uintptr_t)(uint32_t)(a))
extern void syscon_target_logger(uint32_t,const char *,const char *,...);
void syscon_target_protocol_poll(uint32_t context){
    uint8_t uppercase[132];
    for(;;){
        if(!syscon_target_uart_available(B(context)))return;
        uint32_t raw=syscon_target_uart_read(B(context));
        if((int32_t)raw<0){
            uint32_t file=0xba24;
            if(syscon_rt_strrchr(S(file),'/'))file=(uint32_t)(uintptr_t)syscon_rt_strrchr(S(file),'/')+1;
            syscon_target_assert(file,0x4e7,0xbaae);
        }
        uint32_t byte=(uint8_t)raw;
        if(!B(context+13) || byte-10u>116)continue;
        if(!W(context+8))syscon_target_logger(3,S(0xb849),S(0xb896));
        if(B(0x200002ee) && W(context+16)!=(uint32_t)(uintptr_t)syscon_target_mfg_logger)
            syscon_target_logger(1,S(0xb849),S(0xbab8),byte,raw);
        if(B(context+12))syscon_target_uart_put(B(context),byte);
        uint32_t count=W(context+8);
        if(count>=125){
            B(W(context+4)+127)=0;
            uint32_t printer=W(context+16),buffer=W(context+4);
            syscon_target_failure(buffer,0xbabe,(syscon_target_print_callback)(uintptr_t)printer);W(context+8)=0;continue;
        }
        if(byte!=10 && byte!=13){W(context+8)=count+1;B(W(context+4)+count)=(uint8_t)byte;continue;}
        if(count){
            B(W(context+4)+count)=0;
            uint32_t buffer=W(context+4),end=buffer;
            for(;;){uint32_t c=B(end);if(!c)break;if(c==' ')B(end)=':';++end;}
            if(end!=buffer && (B(end-1)!=';' || B(end-2)!=':')){B(end)=':';B(end+1)=';';B(end+2)=0;}
            buffer=W(context+4);uint32_t printer=W(context+16);
            uint32_t args=(uint32_t)(uintptr_t)syscon_rt_strchr(S(buffer),':');
            if(args){++args;if(!syscon_rt_strchr(S(args),':'))args=0;}
            uint32_t index;
            for(index=0;index<37;++index){
                const char *name=S(syscon_target_commands[index].name);
                if(!syscon_rt_strncasecmp(S(buffer),name,syscon_rt_strlen(name)))break;
            }
            if(index==37)syscon_target_failure(buffer,0xbaf9,(syscon_target_print_callback)(uintptr_t)printer);
            else{
                const syscon_target_command_record *record=&syscon_target_commands[index];
                uint32_t policy=record->policy;
                if(policy==1 && !args)syscon_target_failure(buffer,0xbae5,(syscon_target_print_callback)(uintptr_t)printer);
                else if(!policy && args)syscon_target_failure(buffer,0xbace,(syscon_target_print_callback)(uintptr_t)printer);
                else{
                    if(args && record->uppercase){
                        syscon_rt_strncpy(uppercase,S(args),127);
                        for(uint8_t *p=uppercase;*p;++p)*p=(uint8_t)syscon_rt_toupper(*p);
                        args=(uint32_t)(uintptr_t)uppercase;
                    }
                    uint32_t success=record->handler(args,printer);
                    ((void (*)(const char *))(uintptr_t)printer)(S(success?0xbaa9:0xb6c6));
                }
            }
        }
        W(context+8)=0;
    }
}
