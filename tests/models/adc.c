#include "adc.h"
#include <string.h>

static uint32_t get32(const uint8_t *p) {
    return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;
}
static void put32(uint8_t *p,uint32_t value) {
    for (unsigned i=0;i<4;++i)p[i]=(uint8_t)(value>>(i*8));
}
static uint32_t readreg(const syscon_adc_environment *e,uint32_t address) {
    return e->read32(e->ctx,address);
}
static void writereg(const syscon_adc_environment *e,uint32_t address,uint32_t value) {
    e->write32(e->ctx,address,value);
}
static void delay(const syscon_adc_environment *e,uint32_t cycles) {
    e->delay_cycles(e->ctx,cycles);
}
static uint64_t fault(const syscon_adc_environment *e,uint32_t line) {
    e->assertion(e->ctx,line);return UINT64_MAX;
}
static const uint8_t *mapping(const uint8_t *ram,uint8_t pin) {
    for (unsigned i=0;i<6;++i)if (ram[0xf4+i*12]==pin)return ram+0xf4+i*12;
    return 0;
}
static uint32_t raw(const syscon_adc_environment *e,const uint8_t *map) {
    uint32_t base=get32(map+4),ctl=base+0x1100,start=base+0x1104;
    writereg(e,ctl,readreg(e,ctl)&~1U);
    writereg(e,base+0x1180+(uint32_t)map[9]*4,(uint32_t)map[8]|0x1000000);
    writereg(e,ctl,readreg(e,ctl)|1);
    writereg(e,start,readreg(e,start)|0x100);
    delay(e,32000);
    writereg(e,start,readreg(e,start)&~0x100U);
    delay(e,3200);
    return readreg(e,base+0x556280+(uint32_t)map[9]*4)&0xffff;
}

uint64_t syscon_adc_execute(uint8_t ram[4096],const syscon_adc_environment *e,
                           uint32_t entry,uint32_t pin,const uint8_t *config) {
    if (entry==0x7d54) {
        const uint32_t vref=0x40030000,adc=0x40004000,sys=0x40400000;
        if (!ram[0x694]) {
            writereg(e,vref+0x804,0xb1000001);
            writereg(e,vref+0x800,0x26000001);
            writereg(e,vref+0x1008,8);
            writereg(e,vref+0x1000,0);
            /* Driver helper ORs the first two byte fields, not a uint16. */
            writereg(e,vref+0x1100,0x81);
            writereg(e,vref+0x1108,0);
            ram[0x694]=1;
        }
        unsigned tries=100;
        do {
            if (readreg(e,vref+0x1104)&1)break;
            --tries;
            delay(e,320);
        } while (tries);
        if (!(readreg(e,vref+0x1104)&1))return 0x80000000;
        writereg(e,adc+0x1100,readreg(e,adc+0x1100)&~1U);
        writereg(e,adc+0x1180,0x100020b);
        writereg(e,adc+0x1100,readreg(e,adc+0x1100)|1);
        writereg(e,adc+0x1104,readreg(e,adc+0x1104)|0x100);
        delay(e,32000);
        writereg(e,adc+0x1104,readreg(e,adc+0x1104)&~0x100U);
        delay(e,3200);
        uint32_t measured=readreg(e,adc+0x556280);
        uint32_t old=readreg(e,sys+0x1300);
        writereg(e,sys+0x1300,5);
        uint32_t calibrated=readreg(e,0x41c4003c);
        writereg(e,sys+0x1300,old&7);
        if (!calibrated || calibrated==0xfff)return 0x80000000;
        int32_t product=(int32_t)(((measured&0xffff)-calibrated)*14000U);
        return (uint32_t)(product/-7168+300);
    }
    if (entry!=0x7c54 && entry!=0x7e7c && entry!=0x7f24)return UINT64_MAX;
    const uint8_t *map=mapping(ram,(uint8_t)pin);
    if (!map)return fault(e,entry==0x7c54?21:131);
    if (entry==0x7c54) {
        if (!config)return fault(e,22);
        uint32_t base=get32(map+4),old;
        writereg(e,base+0x804,0xb1000003);
        writereg(e,base+0x800,0x26000001);
        old=readreg(e,base+0x808);
        writereg(e,base+0x808,((0xa9000001^old)&0xff000003)^old);
        old=readreg(e,base+0x1100);
        writereg(e,base+0x1100,((0x2000000^old)&0x7000000)^old);
        writereg(e,base+0x1110,5);
        old=readreg(e,base+0x1104);
        writereg(e,base+0x1104,((old^0x100000)&0x130001)^old);
        writereg(e,base+0x1108,readreg(e,base+0x1108)&0xe0e0fff8);
        writereg(e,base+0x1114,0x1a);
        writereg(e,base+0x1100,readreg(e,base+0x1100)|0x10000);
        memcpy(ram+0x685,config,7);
        put32(ram+0x68c,(uint32_t)config[4]|(uint32_t)config[5]<<8);
        return 0;
    }
    uint32_t converted=raw(e,map);
    if (entry==0x7f24) {
        int32_t product=(int32_t)(get32(ram+0x68c)*converted);
        converted=(uint32_t)(product/4096);
    }
    return converted;
}
