/* Runtime namespace compaction/update and initialization at the original ABI. */
#include "config_helpers.h"
#include "runtime_memory.h"
#include <stdint.h>
#define TEXT(a) ((const char *)(uintptr_t)(a))
#define CONF TEXT(0xad0c)
static void feed(void){*(volatile uint32_t *)(uintptr_t)0x40081108=0xa7;}
uint32_t syscon_cfg_compact_body(uint32_t base,const char *key,const char *value,uint32_t original_frame){
    char kept[8][2][31],candidate[31];
    syscon_target_logger(3,CONF,TEXT(0xae6a),0x20001000u-original_frame);
    feed();
    syscon_rt_strncpy(kept[0][0],key,30);kept[0][0][30]=0;
    syscon_rt_strncpy(kept[0][1],value,30);kept[0][1][30]=0;
    syscon_target_logger(3,CONF,TEXT(0xae8f),key,value);
    uint32_t count=1;
    for(int32_t index=14;index>=0;index--){
        const uint8_t *slot=(const uint8_t *)(uintptr_t)(base+(uint32_t)index*64);
        if(slot[0]!=255&&syscon_cfg_field_readable(slot)&&syscon_cfg_checksum(slot)==slot[31]&&syscon_cfg_checksum(slot+32)==slot[63]){
            syscon_rt_strncpy(candidate,slot,30);candidate[30]=0;
            uint32_t existing=0;
            while(existing<count&&syscon_rt_strncmp(kept[existing][0],candidate,30))existing++;
            if(existing==count){
                if(count>7){syscon_target_logger(1,CONF,TEXT(0xaeb5),(count+1)&255,8,15);return 0;}
                syscon_rt_strncpy(kept[count][0],candidate,30);kept[count][0][30]=0;
                syscon_rt_strncpy(kept[count][1],slot+32,30);kept[count][1][30]=0;
                count=(count+1)&255;
            }
        }
        if(!((uint32_t)index&3))feed();
    }
    syscon_target_logger(3,CONF,TEXT(0xaef0),count);feed();
    if(!syscon_cfg_store_erase(base,960)){syscon_target_logger(1,CONF,TEXT(0xaf27));return 0;}
    feed();
    uint32_t result=0;
    for(uint32_t i=0;i<count;i++){
        uint32_t slot=0;
        if(!syscon_cfg_find_slot(base,960,0,0,&slot)){
            syscon_target_logger(1,CONF,TEXT(0xaf4c),i);return 0;
        }
        result=syscon_cfg_write_slot(slot,kept[i][0],kept[i][1]);
        if(!result){syscon_target_logger(1,CONF,TEXT(0xaf87),i,kept[i][0]);return 0;}
        feed();
    }
    syscon_target_logger(3,CONF,TEXT(0xafb7),count);return result;
}
void syscon_cfg_store_init(uint32_t base,uint32_t bytes){
    char version[32];
    if(syscon_cfg_store_get(base,bytes,(char *)TEXT(0xb137),version)){
        syscon_target_logger(3,CONF,TEXT(0xb178),base);return;
    }
    syscon_target_logger(3,CONF,TEXT(0xb143),base);
    (void)syscon_cfg_store_erase(base,bytes);
    (void)syscon_cfg_store_append(base,bytes,TEXT(0xb137),TEXT(0xb3c1));
    if(!syscon_cfg_store_get(base,bytes,(char *)TEXT(0xb137),version)){
        syscon_target_logger(1,CONF,TEXT(0xb219));
        const char *path=TEXT(0xadf5),*file=path;
        if(syscon_rt_strrchr(path,'/'))file=(const char *)syscon_rt_strrchr(path,'/')+1;
        syscon_cfg_assert(file,0x2db,TEXT(0xb422));
    }
}
void syscon_target_config_init(void){
    syscon_cfg_store_init(0xf800,1024);syscon_cfg_store_init(0xfc00,960);syscon_cfg_load();
}
uint32_t syscon_cfg_runtime_update_body(const char *key,const char *value,uint32_t original_frame){
    if(syscon_rt_strlen(key)>=31||syscon_rt_strlen(value)>=31){syscon_target_logger(1,CONF,TEXT(0xb10e));return 0;}
    uint32_t valid=syscon_cfg_field_writable((const uint8_t *)key);
    if(valid)valid=syscon_cfg_field_writable((const uint8_t *)value);
    if(!valid){syscon_target_logger(1,CONF,TEXT(0xb0e8),key);return 0;}
    char previous[32];
    uint32_t result=syscon_cfg_store_get(0xfc00,960,(char *)key,previous);
    if(result&&!syscon_rt_strcmp(previous,value))return result;
    uint32_t slot=0;
    if(!syscon_cfg_find_slot(0xfc00,960,(char *)key,0,&slot)){
        syscon_target_logger(3,CONF,TEXT(0xb1c9));
        result=syscon_cfg_compact_body(0xfc00,key,value,original_frame-584u);
    }else{
        if(!syscon_rt_strlen(value))return 0;
        result=syscon_cfg_write_slot(slot,key,value);
    }
    if(!result)return 0;
    syscon_cfg_load();return valid;
}
