#include "i2c.h"

static uint32_t get32(const uint8_t *p) {
    return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;
}
static uint32_t readreg(const syscon_i2c_environment *e,uint32_t a) {return e->read32(e->ctx,a);}
static void writereg(const syscon_i2c_environment *e,uint32_t a,uint32_t v) {e->write32(e->ctx,a,v);}
static void delay(const syscon_i2c_environment *e,uint32_t cycles) {e->delay_cycles(e->ctx,cycles);}
static void stage(const syscon_i2c_environment *e,uint32_t code) {writereg(e,0x400b040c,code);}
static uint64_t fault(const syscon_i2c_environment *e,uint32_t line) {
    e->assertion(e->ctx,line);return UINT64_MAX;
}
static void tx_flush(const syscon_i2c_environment *e,uint32_t base) {
    writereg(e,base+0x1238,readreg(e,base+0x1238)|0x80);
    while ((readreg(e,base+0x123c)&0xf00)!=0x800) {}
    writereg(e,base+0x1238,readreg(e,base+0x1238)&~0x80U);
}
static void rx_flush(const syscon_i2c_environment *e,uint32_t base) {
    writereg(e,base+0x1238,readreg(e,base+0x1238)|0x8000);
    while (readreg(e,base+0x123c)&15) {}
    writereg(e,base+0x1238,readreg(e,base+0x1238)&~0x8000U);
}
static uint32_t error(const syscon_i2c_environment *e,uint32_t base) {
    writereg(e,base+0x1214,0);tx_flush(e,base);rx_flush(e,base);return 0xffffffff;
}
static int wait_status(const syscon_i2c_environment *e,uint32_t base,uint32_t mask,int set) {
    for (unsigned tries=10000;tries;--tries) {
        if (!!(readreg(e,base+0x1218)&mask)==set)return 1;
        delay(e,32);
    }
    return 0;
}
static void begin_transfer(const syscon_i2c_environment *e,uint32_t base,uint32_t address,uint32_t length) {
    uint32_t old=readreg(e,base+0x1210);
    writereg(e,base+0x1210,((address^old)&0x7ff)^old);
    old=readreg(e,base+0x1214);
    writereg(e,base+0x1214,((((length<<16)|7)^old)&0xfff0007)^old);
}

uint64_t syscon_i2c_execute(uint8_t ram[4096],const syscon_i2c_environment *e,
    uint32_t entry,uint32_t bus,uint32_t address,uint8_t *data,uint32_t length) {
    const uint8_t *map=ram+0x13c;
    uint32_t base=get32(map+4);
    if (entry==0x8798) {
        uint32_t reason=readreg(e,0x400f1020)&255;
        if (reason==8 || reason==11)ram[0x760]=1;
        return 0;
    }
    if (entry==0x82b4)return error(e,base);
    if (entry!=0x82f0 && entry!=0x844c && entry!=0x860c)return UINT64_MAX;
    if (bus)return fault(e,entry==0x82f0?87:entry==0x844c?142:206);
    if (entry==0x82f0) {
        if (!data)return fault(e,88);
        writereg(e,base+0x804,0xb1000003);
        writereg(e,base+0x800,0x26000001);
        delay(e,1000);
        if (map[0]>=25 || map[2]>=25)return UINT64_MAX;
        uint32_t scl=0x40428004+(uint32_t)ram[0x16c+map[0]*8+5]*4;
        uint32_t sda=0x40428004+(uint32_t)ram[0x16c+map[2]*8+5]*4;
        writereg(e,scl,0xc0080|map[1]);
        writereg(e,sda,0xc0080|map[3]);
        writereg(e,scl,readreg(e,scl)|0x2000000);
        writereg(e,sda,readreg(e,sda)|0x2000000);
        uint32_t old=readreg(e,base+0x1004);
        writereg(e,base+0x1004,((8^old)&12)^old);
        old=readreg(e,base+0x1000);
        writereg(e,base+0x1000,((0^old)&7)^old);
        writereg(e,base+0x1224,7);
        writereg(e,base+0x1200,readreg(e,base+0x1200)|0x600);
        writereg(e,base+0x1200,readreg(e,base+0x1200)|0x100);
        writereg(e,base+0x1214,0);
        writereg(e,base+0x1228,readreg(e,base+0x1228)|4);
        if (!data[0]) {
            ram[0x761]=0;
            writereg(e,base+0x1028,readreg(e,base+0x1028)|0x480);
            writereg(e,base+0x1228,readreg(e,base+0x1228)|1);
        }
        if ((int8_t)map[8]>=0) {
            uint32_t bit=1U<<(map[8]&31);
            writereg(e,0xe000e280,bit);writereg(e,0xe000e100,bit);
        }
        return 0;
    }
    if (ram[0x761])return fault(e,entry==0x844c?143:207);
    if (!data && length)return UINT64_MAX;
    if (entry==0x844c) {
        stage(e,9);
        if (!wait_status(e,base,0x20,1))return error(e,base);
        uint32_t empty=0,done=0,result=0;
        int started=0;
        while (done<length) {
            stage(e,10);
            uint32_t free=(readreg(e,base+0x123c)>>8)&15;
            if (!free) {
                if (empty>9999)return error(e,base);
                delay(e,32);++empty;
            } else {
                uint32_t n=length-done;
                if (free<(n&255))n=free;
                n&=255;
                for (unsigned i=0;i<n;++i) {
                    if (!(readreg(e,base+0x123c)&0xf00))break;
                    writereg(e,base+0x1220,data[done+i]);
                }
                empty=0;done=(done+n)&255;
            }
            if (!started) {
                ram[0x760]=0;
                begin_transfer(e,base,address<<1,length);
                stage(e,11);
                if (!wait_status(e,base,0x40,1))return error(e,base);
            }
            started=1;
            if (ram[0x760]) {tx_flush(e,base);result=0xffffffff;break;}
        }
        stage(e,12);
        if (!wait_status(e,base,0x40,0))return error(e,base);
        tx_flush(e,base);
        return ram[0x760]?result:done;
    }
    stage(e,13);
    if (!wait_status(e,base,0x20,1))return error(e,base);
    begin_transfer(e,base,(address<<1)|1,length);
    stage(e,14);
    if (!wait_status(e,base,0x40,1))return error(e,base);
    uint32_t result=0,done=0;
    while (done<length) {
        stage(e,15);
        unsigned tries=10000;
        for (;;) {
            if ((readreg(e,base+0x123c)&15) || ram[0x760])break;
            --tries;delay(e,32);
            if (!tries)return error(e,base);
        }
        if (ram[0x760]) {result=0xffffffff;break;}
        data[done]=(uint8_t)readreg(e,base+0x121c);
        done=(done+1)&255;
    }
    stage(e,16);
    if (!wait_status(e,base,0x40,0))return error(e,base);
    rx_flush(e,base);
    return ram[0x760]?result:length;
}
