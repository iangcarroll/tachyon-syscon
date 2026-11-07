#include "diagnostics.h"
#include <string.h>
static uint32_t r32(const uint8_t *s,unsigned offset){uint32_t v;memcpy(&v,s+offset,4);return v;}
static uint64_t r64(const uint8_t *s,unsigned offset){uint64_t v;memcpy(&v,s+offset,8);return v;}
static void w32(uint8_t *s,unsigned offset,uint32_t v){memcpy(s+offset,&v,4);}
static void w64(uint8_t *s,unsigned offset,uint64_t v){memcpy(s+offset,&v,8);}
static uint64_t call(const syscon_diagnostics_io *io,uint32_t address,uint32_t a){return io->call(io->ctx,address,a);}
void syscon_diagnostics_enable(uint8_t s[4096],uint32_t enable){s[0x46]=(uint8_t)enable;}
void syscon_diagnostics_poll(uint8_t s[4096],const syscon_diagnostics_io *io){
    w64(s,0x2c0,r64(s,0x2c0)+1);
    uint64_t now=call(io,0x77b4,0);
    if(now-(uint64_t)r32(s,0x2c8)<=5000)return;
    uint32_t current=(uint32_t)call(io,0x77b4,0),previous=r32(s,0x2cc);
    uint64_t loops=r64(s,0x2c0);
    w32(s,0x2cc,current);w64(s,0x2c0,0);w32(s,0x2c8,current);
    if(!s[0x46])return;
    uint32_t uptime=(uint32_t)(call(io,0x77b4,0)/1000);
    uint32_t volts[6];
    volts[0]=(uint32_t)call(io,0x4c50,12);
    volts[1]=(uint32_t)call(io,0x4c50,13);
    volts[2]=(uint32_t)call(io,0x4c50,14);
    volts[4]=(uint32_t)call(io,0x4c50,16);
    volts[3]=(uint32_t)call(io,0x4c50,15);
    uint32_t wake=(uint32_t)call(io,0x80f8,17);
    int32_t temperature=(int32_t)call(io,0x7d54,0);
    char text[12];
    if(temperature==INT32_MIN)strcpy(text,"--");
    else{
        uint32_t magnitude=temperature<0?0u-(uint32_t)temperature:(uint32_t)temperature;
        uint32_t whole=magnitude/10;char raw[16],reverse[12];unsigned used=0,n=0;
        if(temperature<0)raw[used++]='-';
        do{reverse[n++]=(char)('0'+whole%10);whole/=10;}while(whole);
        while(n)raw[used++]=reverse[--n];
        raw[used++]='.';raw[used++]=(char)('0'+magnitude%10);raw[used++]='C';
        if(used>11)used=11;
        memcpy(text,raw,used);text[used]=0;
    }
    uint8_t off=(uint8_t)call(io,0x6690,0);
    volts[5]=(uint32_t)call(io,0x55c4,0);
    io->log(io->ctx,0xb253,volts,0);
    uint32_t seconds=(current-previous)/1000;
    uint64_t rate=seconds?loops/seconds:(loops?UINT64_MAX:0);
    uint32_t info[6]={uptime,(uint32_t)(off^1u),(uint32_t)rate,wake?0xcd10:0xcd1d,0,volts[5]};
    io->log(io->ctx,0xb295,info,text);
}
uint32_t syscon_runtime_get(const uint8_t s[4096],uint32_t entry){
    switch(entry){
    case 0x3114:return s[0x30];case 0x3120:return s[0x31];case 0x312c:return s[0x32];
    case 0x3138:return s[0x33];case 0x3144:return s[0x34];case 0x3150:return s[0x35];
    case 0x315c:return r32(s,0x36);case 0x3178:return r32(s,0x3a);
    default:return UINT32_MAX;
    }
}
static int decimal(const char **cursor,uint32_t *out){
    const unsigned char *p=(const unsigned char *)*cursor;
    while(*p==' ' || (*p>=9 && *p<=13))p++;
    int negative=*p=='-';if(*p=='+' || *p=='-')p++;
    uint32_t value=0;int any=0,overflow=0;
    while(*p>='0' && *p<='9'){
        unsigned digit=*p++-'0';any=1;
        if(value>(UINT32_MAX-digit)/10)overflow=1;
        if(!overflow)value=value*10+digit;
    }
    if(!any)return 0;
    *cursor=(const char *)p;*out=overflow?UINT32_MAX:(negative?0u-value:value);return 1;
}
int syscon_hwrevision_new(const char *revision){
    uint32_t major,minor,patch;
    if(!decimal(&revision,&major) || *revision++!='.')return 0;
    if(!decimal(&revision,&minor) || *revision++!='.')return 0;
    if(!decimal(&revision,&patch))return 0;
    return major==1 && minor>1;
}
