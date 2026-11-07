/* Original-ABI namespace entry points, recovered from syscon1.0.52. */
#include "config_helpers.h"
#include "runtime_memory.h"
#define TEXT(a) ((const char *)(uintptr_t)(a))
#define CONF TEXT(0xad0c)
_Static_assert(sizeof(void *)==4,"ARM32 target only");
uint32_t syscon_cfg_indexed_get(uint32_t base,uint32_t bytes,char *key,char *value) {
    if(syscon_rt_strlen(key)>=31){syscon_target_logger(1,CONF,TEXT(0xafe0));return 0;}
    uint32_t slot=0;
    uint32_t found=syscon_cfg_find_slot(base,bytes,key,2,&slot);
    return found?syscon_cfg_read_slot((const uint8_t *)(uintptr_t)slot,value):0;
}
static uint32_t slot_blank(uint32_t base,uint32_t limit,uint32_t index) {
    if(index>=limit)return 1;
    const volatile uint8_t *slot=(const volatile uint8_t *)(uintptr_t)(base+64*index);
    for(unsigned i=0;i<64;i++)if(slot[i]!=255)return 0;
    return 1;
}
uint32_t syscon_cfg_runtime_slot_blank(uint32_t index){return slot_blank(0xfc00,15,index);}
uint32_t syscon_cfg_identity_slot_blank(uint32_t index){return slot_blank(0xf800,16,index);}
uint32_t syscon_cfg_runtime_slot_count(void){return 15;}
uint32_t syscon_cfg_identity_slot_count(void){return 16;}
static void failed_version(uint32_t message,uint32_t line) {
    syscon_target_logger(1,CONF,TEXT(message));
    const char *path=TEXT(0xadf5),*file=path;
    if(syscon_rt_strrchr(path,'/'))file=(const char *)syscon_rt_strrchr(path,'/')+1;
    syscon_cfg_assert(file,line,TEXT(0xb422));
}
uint32_t syscon_cfg_identity_erase(const char *password) {
    if(syscon_rt_strcmp(password,TEXT(0xb1b1))){syscon_target_logger(1,CONF,TEXT(0xb1b8));return 0;}
    if(!syscon_cfg_store_erase(0xf800,1024))return 0;
    uint32_t result=syscon_cfg_store_append(0xf800,1024,TEXT(0xb137),TEXT(0xb3c1));
    char version[32];
    if(!syscon_cfg_store_get(0xf800,1024,(char *)TEXT(0xb137),version))failed_version(0xb219,0x3a4);
    return result;
}
uint32_t syscon_cfg_identity_append(const char *key,const char *value) {
    uint32_t result=syscon_cfg_store_append(0xf800,1024,key,value);
    if(result)syscon_cfg_load();
    return result;
}
uint32_t syscon_cfg_identity_get(char *key,char *out){return syscon_cfg_store_get(0xf800,1024,key,out);}
uint32_t syscon_cfg_identity_indexed_get(char *key,char *out){return syscon_cfg_indexed_get(0xf800,1024,key,out);}
uint32_t syscon_cfg_runtime_get(char *key,char *out){return syscon_cfg_store_get(0xfc00,960,key,out);}
uint32_t syscon_cfg_runtime_erase(const char *password) {
    if(syscon_rt_strcmp(password,TEXT(0xb1f4))){syscon_target_logger(1,CONF,TEXT(0xb1b8));return 0;}
    if(!syscon_cfg_store_erase(0xfc00,960))return 0;
    uint32_t result=syscon_cfg_store_append(0xfc00,960,TEXT(0xb137),TEXT(0xb3c1));
    char version[32];
    if(!syscon_cfg_store_get(0xfc00,960,(char *)TEXT(0xb137),version))failed_version(0xb1fd,0x41a);
    syscon_cfg_load();
    return result;
}
uint32_t syscon_cfg_runtime_indexed_get(char *key,char *out){return syscon_cfg_indexed_get(0xfc00,960,key,out);}
