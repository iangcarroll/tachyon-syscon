#include "format.h"
#include <string.h>
int syscon_sg560d_printf(const syscon_format_memory *memory,const syscon_log_io *io,uint32_t format,uint32_t args) {
    uint8_t buffer[128]={0};
    syscon_format_result result=syscon_vformat(buffer,sizeof(buffer),format,args,memory);
    if(!result.complete)return -1;
    uint32_t length=0;while(buffer[length])length++;
    io->write(io->ctx,1,buffer,length);
    io->write(io->ctx,1,(const uint8_t *)"\r\n",2);
    return 0;
}
typedef struct { const syscon_format_memory *memory;uint8_t args[12]; } prefix_memory;
static int prefix_read(void *ctx,uint32_t address,uint8_t *value) {
    prefix_memory *p=ctx;
    if(address>=0x10000000 && address<0x1000000c){*value=p->args[address-0x10000000];return 1;}
    return p->memory->read_byte(p->memory->ctx,address,value);
}
int syscon_logger(const syscon_format_memory *memory,const syscon_log_io *io,uint8_t enabled,uint32_t level,uint32_t tag,uint32_t format,uint32_t args) {
    if(!enabled)return 0;
    if(io->color(io->ctx)) {
        static const char *const colors[]={"","\x1b[0;31m","\x1b[0;33m","\x1b[0;37m","\x1b[0;34m"};
        if(level>=1 && level<=4)io->write(io->ctx,0,(const uint8_t *)colors[level],7);
    }
    uint64_t time=io->now(io->ctx);
    prefix_memory prefix={memory,{0}};
    for(unsigned i=0;i<8;i++)prefix.args[i]=(uint8_t)(time>>(8*i));
    for(unsigned i=0;i<4;i++)prefix.args[8+i]=(uint8_t)(tag>>(8*i));
    syscon_format_memory overlay={prefix_read,&prefix};
    uint8_t short_buffer[32],large_buffer[256];
    syscon_format_result result=syscon_vformat(short_buffer,32,0xe114,0x10000000,&overlay);
    if(!result.complete)return -1;
    if(result.length>32)return -2;
    io->write(io->ctx,0,short_buffer,result.length);
    result=syscon_vformat(short_buffer,32,format,args,memory);
    if(!result.complete)return -1;
    if(result.length>=1 && result.length<=31)io->write(io->ctx,0,short_buffer,result.length);
    else{
        result=syscon_vformat(large_buffer,256,format,args,memory);
        if(!result.complete)return -1;
        if(result.length){
            uint32_t length=result.length;
            if(length>255){memcpy(large_buffer+252,"...",3);large_buffer[255]=0;length=255;}
            io->write(io->ctx,0,large_buffer,length);
        }
    }
    if(io->color(io->ctx))io->write(io->ctx,0,(const uint8_t *)"\x1b[0m",4);
    io->write(io->ctx,0,(const uint8_t *)"\r\n",2);
    return 0;
}
