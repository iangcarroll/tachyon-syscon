/* Application orchestration reconstructed from0x3b34. The infinite main loop
 * is split into init and one tick for bounded tests; dependency order is kept. */
#include "application.h"
#include <string.h>

static uint32_t r32(const uint8_t *s,unsigned o) { uint32_t v;memcpy(&v,s+o,4);return v; }
static void w32(uint8_t *s,unsigned o,uint32_t v) { memcpy(s+o,&v,4); }
static uint32_t dep(const sg560d_environment *e,uint32_t fn,uint32_t a,uint32_t b) {
    return (uint32_t)e->call(e->ctx,fn,a,b,0,0,0,0);
}
static void stage(const sg560d_environment *e,unsigned n) { dep(e,0x7b78,n,0); }

static void event_queue_init(uint8_t *s,const sg560d_environment *e) {
    w32(s,0x2d8,0x200002d1);w32(s,0x2dc,4);
    w32(s,0x2e4,0);w32(s,0x2e0,0);s[0x2e8]=0;
    e->call(e->ctx,0x969c,0x200002d8,0x3a89,0x2000060c,0,0,0);
}

void syscon_application_constructors(uint8_t s[4096],const sg560d_environment *e) {
    dep(e,0x7a50,0,0);
    w32(s,0x2cc,dep(e,0x77b4,0,0));
    event_queue_init(s,e);
}

uint32_t syscon_application_count(const uint8_t s[4096],uint32_t address) {
    unsigned q=address-0x20000000;
    uint32_t size=r32(s,q+4),write=r32(s,q+8),read=r32(s,q+12);
    if(s[q+16])return size;
    return write<read?write+size-read:write-read;
}

void syscon_application_event(uint8_t s[4096],uint8_t event) {
    if(s[0x2e8]) return; /* Full buffer: original logs and drops new event. */
    uint32_t write=r32(s,0x2e0),size=r32(s,0x2dc);
    s[r32(s,0x2d8)-0x20000000+write]=event;
    write=(write+1)%size;w32(s,0x2e0,write);
    if(write==r32(s,0x2e4))s[0x2e8]=1;
}

static void request_off(uint8_t *s,const sg560d_environment *e) {
    if(!dep(e,0x51c0,0,0))s[0x2ec]=1;
    else dep(e,0x6720,0,0);
}

void syscon_application_init(uint8_t s[4096],const sg560d_environment *e) {
    (void)s;
    dep(e,0x798c,0,0);
    uint32_t previous_stage=dep(e,0x7b88,0,0);
    stage(e,1);dep(e,0x7be0,0,0);
    const uint8_t uart[9]={0,0,9,0,0,0xc2,1,0,0};
    e->call(e->ctx,0x8954,0,0,0,0,uart,sizeof(uart));
    dep(e,0x8fc0,1,0);dep(e,0x59d8,0,0);dep(e,0x776c,0,0);
    dep(e,0x7540,0,0);dep(e,0x79d0,0,0);dep(e,0x30f0,0,0);
    dep(e,0x7910,0,0);dep(e,0x5b7c,0,0);
    uint32_t reset=dep(e,0x7c08,0,0);
    if(reset!=1 && reset!=6)dep(e,0x5afc,0,0);
    dep(e,0x5970,0,0);dep(e,0x5908,0x3a8d,0);dep(e,0x79d0,0,0);
    dep(e,0x3808,reset<2,0);
    dep(e,0x7c3c,reset,0);dep(e,0x7bfc,0,0);dep(e,0x7b9c,previous_stage,0);
    uint32_t mode=dep(e,0x5ac4,0,0);dep(e,0x66a0,mode,0);
    dep(e,0x5af0,0,0);dep(e,0x5b14,0,0);
    dep(e,0x54cc,reset<2,0);
    mode=dep(e,0x5ac4,0,0);dep(e,0x6948,mode,0);
    dep(e,0x4c24,0,0);dep(e,0x79d0,0,0);
    if(reset==1) {
        uint32_t automatic=dep(e,0x3114,0,0);
        if(dep(e,0x3144,0,0))dep(e,0x5c68,7,0);
        else if(automatic)dep(e,0x6428,0,0);
    }
}

void syscon_application_tick(uint8_t s[4096],const sg560d_environment *e) {
    stage(e,2);dep(e,0x3488,0,0);stage(e,3);
    if(!s[0x2ec] && syscon_application_count(s,0x200002d8)) {
        uint8_t event=255;
        if(syscon_application_count(s,0x200002d8)) {
            uint32_t read=r32(s,0x2e4);
            event=s[r32(s,0x2d8)-0x20000000+read];
            w32(s,0x2e4,(read+1)%r32(s,0x2dc));s[0x2e8]=0;
        }
        if(!dep(e,0x3144,0,0)) switch(event) {
        case 0:
            s[0x2ed]=(uint8_t)dep(e,0x6690,0,0);
            dep(e,0x3138,0,0); /* Original first reads for diagnostic text. */
            if(s[0x2ed] && dep(e,0x3138,0,0))dep(e,0x5e24,0,0);
            break;
        case 1:if(s[0x2ed])dep(e,0x6428,0,0);break;
        case 2:
            if(dep(e,0x3138,0,0))dep(e,0x5e24,0,0);
            else if(s[0x2ed])dep(e,0x64a0,0,0);
            else request_off(s,e);
            break;
        case 3:
            if(dep(e,0x3138,0,0)) {
                if(s[0x2ed])dep(e,0x64a0,0,0);
                else request_off(s,e);
            }
            break;
        case 4:if(dep(e,0x3138,0,0) && s[0x2ed])dep(e,0x5e24,0,0);break;
        case 5:if(s[0x2ed] && dep(e,0x3138,0,0))dep(e,0x65e4,0,0);break;
        }
    }
    stage(e,4);dep(e,0x4c14,0,0);stage(e,5);dep(e,0x6a68,0,0);
    dep(e,0x79d0,0,0);stage(e,6);dep(e,0x75d8,0,0);stage(e,7);
    if(s[0x2ec] && !dep(e,0x76d8,0,0)) { s[0x2ec]=0;dep(e,0x6720,1,0); }
    stage(e,8);dep(e,0x7974,0,0);
}

uint64_t syscon_application_helper(uint8_t s[4096],const sg560d_environment *e,uint32_t entry,uint32_t a,uint32_t b) {
    switch(entry) {
    case 0x3610:w32(s,0x2cc,dep(e,0x77b4,0,0));return 0;
    case 0x3ec0:event_queue_init(s,e);return 0;
    case 0x3a8c:syscon_application_event(s,(uint8_t)a);return 0;
    case 0x3ad4:request_off(s,e);return 0;
    case 0x3af4:stage(e,17);e->call(e->ctx,0x8c8c,0,a,b,0,0,0);return 0;
    case 0x3b0c:return syscon_application_count(s,a);
    case 0x4c14:dep(e,0x49d0,0x20000048,0);return 0;
    case 0x78ac:
        if(dep(e,0x6690,0,0)) {
            dep(e,0x77fc,10,0);
            if(!dep(e,0x80f8,a,0))s[0x680]=1;
        }
        return 0;
    case 0x7910: {
        const uint8_t cfg[12]={0};
        e->call(e->ctx,0x7f58,17,0,0,0,cfg,sizeof(cfg));return 0;
    }
    case 0x7928:
        if(a && dep(e,0x3120,0,0))e->call(e->ctx,0x8148,17,2,0x78ad,0,0,0);
        else dep(e,0x81f8,17,0);
        return 0;
    case 0x7974:if(s[0x680]) { dep(e,0x6428,0,0);s[0x680]=0; }return 0;
    default:return UINT64_MAX;
    }
}
