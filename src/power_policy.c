#include "power_policy.h"
#include <stddef.h>

static uint32_t read32(const uint8_t *p) {
    return (uint32_t)p[0] | (uint32_t)p[1]<<8 | (uint32_t)p[2]<<16 | (uint32_t)p[3]<<24;
}
static void write32(uint8_t *p, uint32_t v) {
    for (unsigned i=0;i<4;++i) p[i]=(uint8_t)(v>>(i*8));
}
static uint64_t read64(const uint8_t *p) {
    return read32(p) | (uint64_t)read32(p+4)<<32;
}
static void write64(uint8_t *p,uint64_t value) {
    write32(p,(uint32_t)value);write32(p+4,(uint32_t)(value>>32));
}
static uint64_t call(const syscon_power_policy_environment *e,uint32_t f,uint32_t a) {
    return e->call(e->ctx,f,a,0,NULL,0);
}
static void output(const syscon_power_policy_environment *e,uint32_t printer,
                   uint32_t format,unsigned count,uint32_t a,uint32_t b) {
    uint32_t args[2]={a,b};
    e->call(e->ctx,printer&~1U,format,count,args,count*4);
}
static uint32_t table(const uint8_t *ram,unsigned offset,uint32_t index) {
    /* Report helpers produce hardware enum values in0..2. */
    return read32(ram+offset+index*4);
}

uint64_t syscon_power_policy_execute(uint8_t ram[4096],const syscon_power_policy_environment *e,
                                     uint32_t entry,uint32_t a) {
    switch (entry) {
    case 0x5358: {
        int32_t vph=(int32_t)call(e,0x4c50,12);
        uint32_t header=(uint32_t)call(e,0x4c50,13);
        uint32_t battery=(uint32_t)call(e,0x4c50,14);
        int32_t usb=(int32_t)call(e,0x4c50,16);
        int32_t v18=(int32_t)call(e,0x4c50,15);
        uint32_t vbatt=(uint32_t)call(e,0x4ca8,0);
        uint32_t batt=(uint32_t)call(e,0x5af0,0);
        uint32_t vbus=(uint32_t)call(e,0x4d00,0);
        uint32_t hdr=(uint32_t)call(e,0x4d9c,0);
        if (vbatt>(4096-0x78-4)/4 || batt>(4096-0x6c-4)/4 ||
            vbus>(4096-0x84-4)/4 || hdr>(4096-0x60-4)/4) return UINT64_MAX;
        output(e,a,0xcb61,0,0,0);
        output(e,a,0xcb76,2,table(ram,0x6c,batt),battery);
        uint32_t id=(uint32_t)call(e,0x4d58,0);
        output(e,a,0xcb91,1,id==1?0xcb23:0xcb2c,0);
        uint32_t ntc=(uint32_t)call(e,0x4df4,0);
        if (ntc>987) return UINT64_MAX;
        output(e,a,0xcba5,1,table(ram,0x90,ntc),0);
        output(e,a,0xcbb9,2,usb>4499?0xcb34:0xcb3d,(uint32_t)usb);
        uint32_t removed=(uint32_t)call(e,0x3620,0x20);
        output(e,a,0xcbd4,1,removed?0xcb46:0xcb54,0);
        output(e,a,0xcbe8,2,table(ram,0x60,hdr),header);
        uint32_t boost=(uint32_t)call(e,0x4ec4,0);
        output(e,a,0xcc03,1,boost?0xb9f9:0xba07,0);
        output(e,a,0xcc17,1,table(ram,0x84,vbus),0);
        output(e,a,0xcc2b,1,table(ram,0x78,vbatt),0);
        output(e,a,0xcc3f,2,v18>1700?0xd1a9:0xd776,(uint32_t)v18);
        output(e,a,0xcc5e,2,vph>3000?0xd1a9:0xd776,(uint32_t)vph);
        output(e,a,0xcc7d,0,0,0);
        return 0;
    }
    case 0x54cc: {
        const uint8_t adc[7]={0,0,7,0,8,7,12};
        const uint8_t pins[6]={12,13,14,15,16,23};
        for (unsigned i=0;i<6;++i)e->call(e->ctx,0x7c54,pins[i],0,adc,7);
        if (!a) syscon_power_policy_execute(ram,e,0x5358,0x8fa1);
        else {
            const uint8_t low[9]={8,9,10,12,13,0,15,7,1};
            const uint8_t high[3]={2,3,11};
            uint8_t config[3]={1,0,1};
            for (unsigned i=0;i<9;++i)e->call(e->ctx,0x386c,low[i],0,config,3);
            config[1]=1;
            for (unsigned i=0;i<3;++i)e->call(e->ctx,0x386c,high[i],0,config,3);
        }
        return 0;
    }
    case 0x559c: {
        int32_t measured=(int32_t)call(e,0x4c50,12);
        if (measured<(int32_t)read32(ram+0x5c))write32(ram+0x5c,(uint32_t)measured);
        return 0;
    }
    case 0x55b4:write32(ram+0x5c,0x7fffffff);return 0;
    case 0x55c4: {
        uint32_t value=read32(ram+0x5c);
        return value==0x7fffffff?0xffffffff:value;
    }
    case 0x55dc:
        ram[0x36f]=(uint8_t)a;ram[0x380]=0;
        write64(ram+0x388,a?call(e,0x77b4,0):0);
        return 0;
    case 0x562c:return ram[0x36f];
    case 0x5638: {
        uint64_t start=read64(ram+0x388);
        if (!start)return 0;
        uint64_t now=call(e,0x77b4,0);
        return now>start?now-start:0;
    }
    case 0x5670:return ram[0x380];
    case 0x567c:return ram[0x380]?0:ram[0x36f];
    case 0x5694: {
        uint8_t reason=ram[0x36f];
        uint64_t start=read64(ram+0x388);
        uint64_t now=call(e,0x77b4,0);
        if (!ram[0x380] && reason && start && now-start>299999)ram[0x380]=1;
        return 0;
    }
    default:return UINT64_MAX;
    }
}
