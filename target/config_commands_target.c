/* Original-ABI configuration command handlers with real scan/store helpers. */
#include "config_commands_target.h"
#include "config_helpers.h"
#include "diagnostics_target.h"
#include "runtime_scan.h"
#include "runtime_memory.h"
#include "mspm0_core_target.h"
#include <stdint.h>
#define S(a) ((const char *)(uintptr_t)(uint32_t)(a))
typedef void (*printer_t)(const char *,...);
typedef uint32_t (*get_t)(char *,char *);
typedef uint32_t (*set_t)(const char *,const char *);
static uint32_t get(uint32_t arguments,uint32_t printer,get_t lookup,uint32_t found){
    char key[32],value[32];printer_t print=(printer_t)(uintptr_t)printer;
    if(syscon_rt_sscanf(S(arguments),S(0xb9d2),key)!=1){print(S(0xb709));return 0;}
    uint32_t result=lookup(key,value);
    if(result)print(S(found),key,value);else print(S(0xb951),key);
    return result;
}
/* A separate helper adds an observable eight-byte frame: compaction logs the
 * original stack usage. Keep the handler's original single 80-byte frame. */
__attribute__((always_inline)) static inline uint32_t set(uint32_t arguments,uint32_t printer,set_t append){
    char key[32],value[32];printer_t print=(printer_t)(uintptr_t)printer;
    if(syscon_rt_sscanf(S(arguments),S(0xb9ca),key,value)!=2){print(S(0xb709));return 0;}
    uint32_t result=append(key,value);
    if(result)print(S(0xb949),key,value);else print(S(0xb9db),key);
    return result;
}
static uint32_t erase(uint32_t arguments,uint32_t printer,uint32_t (*erase_store)(const char *),uint32_t success){
    char password[32];printer_t print=(printer_t)(uintptr_t)printer;
    if(syscon_rt_sscanf(S(arguments),S(0xb9d2),password)!=1){print(S(0xb709));return 0;}
    uint32_t result=erase_store(password);print(S(result?success:0xb1b8));return result;
}
uint32_t syscon_target_cmd_config_id_find(uint32_t a,uint32_t p){return get(a,p,syscon_cfg_identity_indexed_get,0xb942);}
uint32_t syscon_target_cmd_config_find(uint32_t a,uint32_t p){return get(a,p,syscon_cfg_runtime_indexed_get,0xb942);}
uint32_t syscon_target_cmd_config_id_get(uint32_t a,uint32_t p){return get(a,p,syscon_cfg_identity_get,0xb949);}
uint32_t syscon_target_cmd_config_get(uint32_t a,uint32_t p){return get(a,p,syscon_cfg_runtime_get,0xb949);}
uint32_t syscon_target_cmd_config_id_set(uint32_t a,uint32_t p){return set(a,p,syscon_cfg_identity_append);}
uint32_t syscon_target_cmd_config_set(uint32_t a,uint32_t p){return set(a,p,syscon_cfg_runtime_update);}
uint32_t syscon_target_cmd_config_id_erase(uint32_t a,uint32_t p){return erase(a,p,syscon_cfg_identity_erase,0xb9b3);}
uint32_t syscon_target_cmd_config_erase(uint32_t a,uint32_t p){return erase(a,p,syscon_cfg_runtime_erase,0xb9e7);}
void syscon_target_config_dump(uint32_t identity,uint32_t printer){
    printer_t print=(printer_t)(uintptr_t)printer;char key[32]={0},value[32];
    uint32_t count=identity?syscon_cfg_identity_slot_count():syscon_cfg_runtime_slot_count();
    uint32_t rejected=0;
    for(uint32_t index=0;index!=count;++index){
        syscon_rt_snprintf(key,32,S(0xb1ae),index);
        uint32_t found=identity?syscon_cfg_identity_indexed_get(key,value):syscon_cfg_runtime_indexed_get(key,value);
        if(found)print(S(0xb949),key,value);
        else{
            uint32_t blank=identity?syscon_cfg_identity_slot_blank(index):syscon_cfg_runtime_slot_blank(index);
            if((uint8_t)blank!=1){print(S(0xb95f),index);++rejected;}
        }
        syscon_target_watchdog_feed();syscon_rt_memset(value,0,32);
    }
    print(S(0xb970));if(rejected)print(S(0xb983),rejected);
}
uint32_t syscon_target_cmd_config_id_dump(uint32_t arguments,uint32_t printer){(void)arguments;syscon_target_config_dump(1,printer);return 1;}
uint32_t syscon_target_cmd_config_dump(uint32_t arguments,uint32_t printer){(void)arguments;syscon_target_config_dump(0,printer);return 1;}
uint32_t syscon_target_cmd_config_internal(uint32_t arguments,uint32_t printer){
    (void)arguments;printer_t print=(printer_t)(uintptr_t)printer;
    uint32_t flags[6];flags[0]=syscon_target_auto_boot();flags[1]=syscon_target_wakeup_enabled();
    flags[2]=syscon_target_log_color();flags[3]=syscon_target_alt_powerkey();
    flags[4]=syscon_target_factory_test();flags[5]=syscon_target_modem_always_on();
    uint32_t long_seconds=syscon_target_powerkey_long_seconds(),extra_seconds=syscon_target_powerkey_extra_seconds();
    const uint32_t formats[]={0xb73c,0xb74e,0xb766,0xb781,0xb79a,0xb7af};
    for(unsigned i=0;i<6;++i)print(S(formats[i]),S(flags[i]?0xafed:0xae64));
    print(S(0xb7ca),long_seconds);print(S(0xb7dc),extra_seconds);return 1;
}
