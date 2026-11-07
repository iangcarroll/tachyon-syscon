/* Original config storage path; exposed write-slot frame lives in ARM ABI glue. */
#include "config_helpers.h"
#include "runtime_memory.h"
#include "runtime_scan.h"
#include "flash_controller.h"
#define PTR(a) ((const char *)(uintptr_t)(a))
#define FLASH 0x400cd000u
static uint32_t read_register(void *ctx,uint32_t address){(void)ctx;return *(volatile uint32_t *)(uintptr_t)address;}
#ifdef SYSCON_DIRECT_FLASH_ABI
#include "flash_abi_target.h"
#define CTL_UNPROTECT() syscon_target_flash_unprotect(FLASH)
#define CTL_ERASE(address,size) syscon_target_flash_erase(FLASH,(address),(size))
#define CTL_BLANK(address) syscon_target_flash_blank(FLASH,(address))
#define CTL_PROGRAM(address,data) syscon_target_flash_program(FLASH,(address),(uint32_t)(uintptr_t)(data))
#else
static void write_register(void *ctx,uint32_t address,uint32_t value){(void)ctx;*(volatile uint32_t *)(uintptr_t)address=value;}
static const syscon_flash_controller_io io={0,read_register,write_register};
#define CTL_UNPROTECT() syscon_flash_unprotect_main(&io,FLASH)
#define CTL_ERASE(address,size) syscon_flash_erase(&io,FLASH,(address),(size))
#define CTL_BLANK(address) syscon_flash_blank(&io,FLASH,(address))
#define CTL_PROGRAM(address,data) syscon_flash_program(&io,FLASH,(address),(data))
#endif
void syscon_cfg_flash_report(void){
    uint32_t text;
    switch(read_register(0,FLASH+0x13d0)&0x10f0){
    case 0:text=0xacfa;break;case 0x10:text=0xad11;break;
    case 0x20:text=0xad34;break;case 0x40:text=0xad50;break;
    case 0x80:text=0xad6f;break;case 0x1000:text=0xad8e;break;
    default:text=0xada7;break;
    }
    syscon_target_logger(1,PTR(0xad0c),PTR(text));
}
uint32_t syscon_cfg_store_erase(uint32_t base,uint32_t bytes){
    uint32_t offset=0;
    do{
        CTL_UNPROTECT();
        if(CTL_ERASE(base+offset,64)!=3){syscon_cfg_flash_report();return 0;}
        offset+=64;
    }while(offset<bytes);
    return 1;
}
uint32_t syscon_cfg_prepare_slot(uint32_t address){
    CTL_UNPROTECT();
    if(CTL_BLANK(address)!=3){syscon_cfg_flash_report();return 0;}
    return 1;
}
uint32_t syscon_cfg_finish_slot(uint32_t address,uint8_t *slot){
    slot[31]=syscon_cfg_checksum(slot);slot[63]=syscon_cfg_checksum(slot+32);
    (void)syscon_cfg_slot_valid(slot);
    for(unsigned offset=0;offset<64;offset+=8){
        CTL_UNPROTECT();
        if(CTL_PROGRAM(address+offset,slot+offset)!=3){syscon_cfg_flash_report();return 0;}
    }
    (void)syscon_cfg_slot_valid((const uint8_t *)(uintptr_t)address);
    return 1;
}
uint32_t syscon_cfg_store_append(uint32_t base,uint32_t bytes,const char *key,const char *value){
    if(!syscon_cfg_field_writable((const uint8_t *)key)||!syscon_cfg_field_writable((const uint8_t *)value)){
        syscon_target_logger(1,PTR(0xad0c),PTR(0xb0e8),key);return 0;
    }
    if(syscon_rt_strlen(key)>=31||syscon_rt_strlen(value)>=31){syscon_target_logger(1,PTR(0xad0c),PTR(0xb10e));return 0;}
    uint32_t slot=0;
    if(!syscon_cfg_find_slot(base,bytes,(char *)key,0,&slot)){syscon_target_logger(1,PTR(0xad0c),PTR(0xb124));return 0;}
    return syscon_cfg_write_slot(slot,key,value);
}
void syscon_cfg_bool_get(uint32_t base,char *key,uint8_t *out){
    char value[32]={0};
    if(!syscon_cfg_store_get(base,960,key,value))return;
    if(!syscon_rt_strcmp(value,PTR(0xafed))||!syscon_rt_strcmp(value,PTR(0xb3c1)))*out=1;
    else if(!syscon_rt_strcmp(value,PTR(0xae64))||!syscon_rt_strcmp(value,PTR(0xb422)))*out=0;
    else syscon_target_logger(1,PTR(0xad0c),PTR(0xaff2),key);
}
void syscon_cfg_u32_get(uint32_t base,char *key,uint32_t *out){
    char value[32]={0},*end=0;
    if(!syscon_cfg_store_get(base,960,key,value))return;
    int32_t result=syscon_rt_strtol(value,&end,10);
    if(end==value||*end||result<0)syscon_target_logger(1,PTR(0xad0c),PTR(0xb014),key);
    else *out=(uint32_t)result;
}
static void packed32(uint8_t *p,uint32_t value){for(unsigned i=0;i<4;i++)p[i]=(uint8_t)(value>>(8*i));}
void syscon_cfg_load(void){
    uint8_t *state=(uint8_t *)(uintptr_t)0x20000030;
    syscon_rt_memcpy(state,PTR(0xb236),22);
    static const uint32_t keys[]={0xb036,0xb044,0xb058,0xb06f,0xb084,0xb095};
    for(unsigned i=0;i<6;i++)syscon_cfg_bool_get(0xfc00,(char *)PTR(keys[i]),state+i);
    for(unsigned i=0;i<2;i++){
        uint32_t value=3;syscon_cfg_u32_get(0xfc00,(char *)PTR(i?0xb0ba:0xb0ac),&value);
        if(value<3)value=3;else if(value>30)value=30;
        packed32(state+6+4*i,value);
    }
    char hardware[32];
    if(!syscon_cfg_store_get(0xf800,1024,(char *)PTR(0xb0dc),hardware))syscon_target_logger(1,PTR(0xad0c),PTR(0xb0cd));
    else{syscon_rt_strncpy(state+14,hardware,8);state[21]=0;}
}
