/* Source-backed read/search path; mode1 intentionally ignores validity result. */
#include "config_helpers.h"
#include "config_text.h"
#include "runtime_memory.h"
#include "runtime_support.h"
#include "runtime_scan.h"
#define CONF SYSCON_CFG_LOG_TAG
uint32_t syscon_cfg_field_readable(const uint8_t *field) {
    for(unsigned i=0;i<31;i++){
        uint32_t c=field[i];if(!c||c==';')return 1;
        if(!syscon_rt_isalnum(c)&&c!='_'&&(uint32_t)(c-'-')>1)return 0;
    }
    return 0;
}
uint32_t syscon_cfg_field_writable(const uint8_t *field) {
    return syscon_cfg_field_readable(field)&&!syscon_rt_strchr(field,';');
}
uint32_t syscon_cfg_checksum(const uint8_t *field) {
    uint32_t result=0;for(unsigned i=0;i<31;i++)result^=field[i];return result;
}
uint32_t syscon_cfg_slot_valid(const uint8_t *slot) {
    if(!syscon_cfg_field_readable(slot)||!syscon_cfg_field_readable(slot+32))return 0;
    /* Original snapshots both stored bytes before either checksum loop. These
     * accesses must remain byte reads in this order even if memory changes. */
    uint8_t key_checksum=*(const volatile uint8_t *)(slot+31);
    uint8_t value_checksum=*(const volatile uint8_t *)(slot+63);
    if(key_checksum!=syscon_cfg_checksum(slot)){
        syscon_target_logger(1,CONF,SYSCON_CFG_KEY_CHECKSUM_MISMATCH);return 0;
    }
    uint32_t checksum=syscon_cfg_checksum(slot+32);
    if(value_checksum!=checksum){
        /* The failure diagnostic deliberately rereads the live stored byte. */
        syscon_target_logger(1,CONF,SYSCON_CFG_VALUE_CHECKSUM_MISMATCH,checksum,
                             *(const volatile uint8_t *)(slot+63));return 0;
    }
    return 1;
}
uint32_t syscon_cfg_read_slot(const uint8_t *slot,char *out) {
    (void)syscon_cfg_slot_valid(slot);
    void *copied=syscon_rt_strncpy(out,slot+32,32);out[30]=0;
    char *delimiter=syscon_rt_strchr(out,';');if(delimiter)*delimiter=0;
    return copied!=0;
}
uint32_t syscon_cfg_find_slot(uint32_t base,uint32_t bytes,char *key,uint32_t mode,uint32_t *out) {
    uint32_t length=key?syscon_rt_strlen(key):0,count=bytes>>6;
    *(volatile uint32_t *)(uintptr_t)0x40081108=0xa7;
    if(mode==0){
        uint32_t slot=base,end=base+(count<<6);
        do{
            unsigned i=0;for(;i<64;i++)if(*(const uint8_t *)(uintptr_t)(slot+i)!=255)break;
            if(i==64){*out=slot;return 1;}
            slot+=64;
        }while(slot!=end);
    }else if(mode==1){
        if(!key||!length){
            const char *path=SYSCON_CFG_ORIGINAL_SOURCE_PATH,*file=path;
            if(syscon_rt_strrchr(path,'/'))file=(const char *)syscon_rt_strrchr(path,'/')+1;
            syscon_cfg_assert(file,0x174,SYSCON_CFG_FALSE);
        }else do{
            count--;const uint8_t *slot=(const uint8_t *)(uintptr_t)(base+(count<<6));
            char diagnostic[32];syscon_rt_snprintf(diagnostic,32,SYSCON_CFG_SLOT_DIAGNOSTIC,count);
            (void)syscon_cfg_slot_valid(slot);
            uint32_t i=0;while(i<length+1u&&slot[i]==(uint8_t)key[i])i++;
            if(i>=length+1u){*out=(uint32_t)(uintptr_t)slot;return 1;}
        }while(count);
    }else{
        uint32_t index=(uint32_t)syscon_rt_atoi(key);
        if(index<count){
            const uint8_t *slot=(const uint8_t *)(uintptr_t)(base+(index<<6));
            uint32_t valid=syscon_cfg_slot_valid(slot);
            if(valid){syscon_rt_strncpy(key,slot,32);key[30]=0;char *delimiter=syscon_rt_strchr(key,';');if(delimiter)*delimiter=0;*out=(uint32_t)(uintptr_t)slot;return valid;}
        }else syscon_target_logger(1,CONF,SYSCON_CFG_INVALID_INDEX);
    }
    return 0;
}
uint32_t syscon_cfg_store_get(uint32_t base,uint32_t bytes,char *key,char *out) {
    if(syscon_rt_strlen(key)>=31){syscon_target_logger(1,CONF,SYSCON_CFG_KEY_TOO_LONG);return 0;}
    uint32_t slot=0;
    return syscon_cfg_find_slot(base,bytes,key,1,&slot)?syscon_cfg_read_slot((const uint8_t *)(uintptr_t)slot,out):0;
}
