/* Register-access reconstruction, not a physical MSPM0 peripheral simulation. */
#include "model_memory.h"
#include "mspm0_core.h"
#include <string.h>

static uint32_t read_reg(const mspm0_environment *e,uint32_t a) { return e->read(e->ctx,a); }
static void write_reg(const mspm0_environment *e,uint32_t a,uint32_t v) { e->write(e->ctx,a,v); }
static uint32_t bitmask(unsigned b) { return b<32?UINT32_C(1)<<b:0; }

void mspm0_reset_init(uint8_t ram[4096],const uint8_t *flash,const mspm0_environment *e) {
    memcpy(ram+0x30,flash+0xe2e8,0x290);
    memcpy(ram,flash+0xaaf0,0x30);
    memset(ram+0x2c0,0,0x560);
    e->dispatch(e->ctx,0x96d4,0,0); /* C/C++ constructor runner */
    e->dispatch(e->ctx,0x3b34,0,0); /* Main must normally not return. */
    e->dispatch(e->ctx,0x7bb8,0,0); /* Fault path if main does return. */
}

uint64_t mspm0_core_execute(uint8_t s[4096],const mspm0_environment *e,uint32_t entry,
    uint32_t pin,uint32_t a,uint32_t b,uint32_t c,const uint8_t *cfg) {
    if(entry==0x798c) {
        write_reg(e,0x40080804,0xb1000003);
        write_reg(e,0x40080800,0x26000001);
        write_reg(e,0x40081104,0xbe000000);
        write_reg(e,0x40081100,0xc9020033);
        write_reg(e,0x40081108,0xa7);
        return 0;
    }
    if(entry==0x79d0) { write_reg(e,0x40081108,0xa7);return 0; }
    if(entry==0x7a50)return 0;
    if(entry==0x7a54)return pin<25?0x2000016c+pin*8:0;
    if(entry==0x7be0) { write_reg(e,0x400b0104,read_reg(e,0x400b0104)|0x1000);return 0; }
    if(entry==0x7bfc)return s[0x254];
    if(entry==0x7c08) {
        static const uint8_t mapping[21]={1,5,3,0,6,3,3,3,3,3,3,3,3,2,3,3,3,3,2,4,4};
        if(s[0x254]==255)s[0x254]=(uint8_t)(read_reg(e,0x400b0220)&31);
        unsigned index=(uint8_t)(s[0x254]-1);
        return index<21?mapping[index]:3;
    }
    if(entry==0x7c3c) {
        static const uint32_t names[7]={0xde7b,0xde7f,0xde83,0xde87,0xde92,0xdea1,0xdeab};
        return pin<7?names[pin]:0xcceb;
    }
    if(entry==0x8258) {
        if(read_reg(e,0x40401130)==1) {
            uint32_t index=(read_reg(e,0x400a1020)-1)&255;
            for(unsigned i=0;i<25;++i) {
                unsigned descriptor=0x16c+i*8;
                if(model_read_u32(s,descriptor)==0x400a0000 && s[descriptor+4]==index) {
                    uint32_t fn=model_read_u32(s,0x698+i*8);
                    if(fn)e->dispatch(e->ctx,fn,i,model_read_u32(s,0x69c+i*8));
                    break;
                }
            }
        }
        return 0;
    }
    /* The original asserts nonreturningly for these invalid arguments.
     * This host analysis entry rejects them instead of dereferencing address0.
     * Fault logging/reset semantics remain a separate reconstruction task. */
    if(pin>=25 || (entry==0x7f58 && !cfg))return UINT64_MAX;
    unsigned descriptor=0x16c+pin*8;
    uint32_t port=model_read_u32(s,descriptor),physical=s[descriptor+4];
    uint32_t mask=bitmask(physical),mux=0x40428004+s[descriptor+5]*4;
    switch(entry) {
    case 0x7f58:
        write_reg(e,port+0x800,0x26000001);
        if(cfg[4]==0) {
            write_reg(e,port+0x12e0,mask);
            if(cfg[5]==1)write_reg(e,mux,0xe0081);
            else if(cfg[5]==2)write_reg(e,mux,0xd0081);
            else {
                write_reg(e,mux,0x40081);
                write_reg(e,mux,read_reg(e,mux)|0x2000000);
            }
        } else if(cfg[4]==1) {
            write_reg(e,mux,0x81);
            if(model_read_u32(cfg,8)&2)write_reg(e,port+(cfg[7]?0x1290:0x12a0),mask);
            write_reg(e,port+0x12d0,mask);
        }
        return 0;
    case 0x8054:write_reg(e,port+(a?0x1290:0x12a0),mask);return 0;
    case 0x80ac:write_reg(e,port+0x12b0,mask);return 0;
    case 0x80f8:return (read_reg(e,port+0x1380)&mask)!=0;
    case 0x8148: {
        model_write_u32(s,0x698+pin*8,b);model_write_u32(s,0x69c+pin*8,c);
        uint32_t edge=(a==1 || a==2)?a:3;
        uint32_t reg=port+(physical<16?0x1390:0x13a0);
        unsigned shift=((physical<16?physical:physical-16)*2)&255;
        uint32_t field=shift<32?3u<<shift:0;
        write_reg(e,reg,read_reg(e,reg)&~field);
        write_reg(e,reg,read_reg(e,reg)|(shift<32?edge<<shift:0));
        write_reg(e,port+0x1048,read_reg(e,port+0x1048)|mask);
        write_reg(e,port+0x1028,read_reg(e,port+0x1028)|mask);
        write_reg(e,0xe000e100,2);
        return (uint64_t)pin<<32;
    }
    case 0x81f8:
        model_write_u32(s,0x698+pin*8,0);model_write_u32(s,0x69c+pin*8,0);
        write_reg(e,port+0x1028,read_reg(e,port+0x1028)&~mask);
        return 0;
    default:return UINT64_MAX;
    }
}
