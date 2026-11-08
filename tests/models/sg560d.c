/* Recovered SG560D control helpers. All voltages/times are original integers. */
#include "model_memory.h"
#include "sg560d.h"
#include <string.h>

static uint64_t dep(const sg560d_environment *e,uint32_t f,uint32_t a,uint32_t b) {
    return e->call(e->ctx,f,a,b,0,0,0,0);
}
static uint64_t now(const sg560d_environment *e) { return dep(e,0x77b4,0,0); }
static void assertion(const sg560d_environment *e,uint32_t line,uint32_t condition) {
    /* The real assertion handler does not return. Test adapters record it. */
    e->call(e->ctx,0x2678,0xcfa0,line,condition,0,0,0);
}
static void configure(const sg560d_environment *e,uint32_t function,uint32_t pin,
                      const void *payload,size_t length) {
    e->call(e->ctx,function,pin,0,0,0,payload,length);
}
static void uart_stop(uint8_t *s,const sg560d_environment *e) {
    if(s[0xed]) {
        if(dep(e,0x8b50,1,0)) assertion(e,0x105,0xcfab);
        memset(s+0x3d0,0,128);s[0xed]=0;
    }
    const uint8_t cfg[12]={0,0,0,0,0,2,0,0,0,0,0,0};
    /* hal_uart_info(1) is the fixed RAM descriptor at0x20000244. */
    configure(e,0x7f58,s[0x244],cfg,sizeof(cfg));
    configure(e,0x7f58,s[0x247],cfg,sizeof(cfg));
}
static void uart_start(uint8_t *s,const sg560d_environment *e) {
    if(s[0xed]) return;
    const uint8_t cfg[9]={0,0,9,0,0,0xc2,1,0,0};
    if(e->call(e->ctx,0x8954,1,0,0,0,cfg,sizeof(cfg))) assertion(e,0xf8,0xcfab);
    memset(s+0x3d0,0,128);s[0xed]=1;
}
static void pins_off(const sg560d_environment *e) {
    const uint8_t gpio[12]={0};
    const uint8_t expander[3]={0,0,1};
    configure(e,0x7f58,8,gpio,sizeof(gpio));configure(e,0x7f58,11,gpio,sizeof(gpio));
    configure(e,0x386c,14,expander,sizeof(expander));configure(e,0x386c,4,expander,sizeof(expander));
}
static void pins_on(uint8_t *s,const sg560d_environment *e) {
    uint8_t gpio[12]={0,0,0,0,1,0,0,0,2,0,0,0};
    const uint8_t expander[3]={1,1,1};
    configure(e,0x7f58,8,gpio,sizeof(gpio));configure(e,0x7f58,11,gpio,sizeof(gpio));
    configure(e,0x386c,14,expander,sizeof(expander));configure(e,0x386c,4,expander,sizeof(expander));
    gpio[4]=0;gpio[5]=2;
    for(unsigned pin=18;pin<=20;++pin) configure(e,0x7f58,pin,gpio,sizeof(gpio));
    uart_stop(s,e);
}
static uint32_t power_check(uint8_t *s,const sg560d_environment *e) {
    int32_t battery=(int32_t)dep(e,0x5274,0,0);
    int32_t source=(int32_t)dep(e,0x4ca8,0,0);
    if((int32_t)dep(e,0x4c50,15,0)>1699) assertion(e,0x152,0xae64);
    if(!dep(e,0x3194,0,0) && source!=0) assertion(e,0x159,0xd04d);
    uint32_t direction=(uint32_t)dep(e,0x4d9c,0,0);
    int32_t header=(int32_t)dep(e,0x4c50,13,0);
    int32_t vbat=(int32_t)dep(e,0x4c50,14,0);
    int input=header>4500 && direction<2;
    int32_t usb=(int32_t)dep(e,0x4c50,16,0);
    dep(e,0x4ee0,input?1:2,0);
    if(battery==1) {
        if(vbat<2000) {
            if(dep(e,0x3194,0,0)) { dep(e,0x4e34,2,0);s[0x4f8]=1; }
        } else dep(e,0x4e34,1,0);
    } else dep(e,0x4e34,2,0);
    dep(e,0x5048,usb<=4499 && input && battery==1?2:1,0);
    dep(e,0x5358,0x8fa1,0);
    s[0x4f2]=1;model_write_u64(s,0x518,now(e)+3000);
    return 1;
}
static const uint32_t backoff_base[7]={30000,900000,900000,5000,120000,120000,10000};
static const uint32_t boot_tasks[38]={
    0,0x68fd,1,2000,0,0x6231,
    0,0x68a5,1,2000,0,0x6241,0,0x61f1,
    0,0x6839,1,2000,0,0x6239,1,100,0,0x61d1,1,5000,
    0,0x74c9,1,200,0,0x74a9,1,200,0,0x7489,0,0x61b9
};

static uint32_t retry_delay(const sg560d_environment *e,uint32_t reason,uint32_t attempts) {
    int32_t temperature=(int32_t)dep(e,0x7d54,0,0);
    uint32_t delay=reason<7?backoff_base[reason]:900000;
    if(temperature>=500 && delay<120000) delay=120000;
    for(uint32_t i=0;i!=attempts;++i) {
        if(delay>449999) return 900000;
        delay*=2;
    }
    return delay;
}

static void schedule_retry(uint8_t *s,const sg560d_environment *e,uint32_t reason) {
    int continuing=s[0x508]!=0 && s[0x528]==reason;
    s[0x528]=(uint8_t)reason;
    if(reason==0 || reason-3<4) {
        if(!continuing) model_write_u32(s,0x4f4,0);
        s[0x508]=1;
        uint32_t delay=retry_delay(e,reason,model_read_u32(s,0x4f4));
        model_write_u64(s,0x500,now(e)+delay);
    }
}

static void set_mode(uint8_t *s,const sg560d_environment *e,uint32_t mode) {
    s[0x450]=(uint8_t)mode;
    dep(e,0x5aa8,mode,0);
    uint32_t pwrkey=0;
    switch(mode) {
    case 1: dep(e,0x5c68,0,0);pwrkey=1;break;
    case 2: dep(e,0x5c68,4,0);break;
    case 3: dep(e,0x5c68,1,0);pwrkey=1;break;
    case 4: dep(e,0x5c68,2,0);pwrkey=1;break;
    case 5: dep(e,0x5c68,3,0);break;
    }
    dep(e,0x591c,pwrkey,0);
}

static uint32_t power_on(uint8_t *s,const sg560d_environment *e,uint32_t which) {
    if(s[0x4f1]) return UINT32_MAX;
    dep(e,0x55dc,0,0);
    s[0x508]=0;s[0x528]=0;
    dep(e,0x6282,0,0);
    dep(e,0x7928,0,0);
    unsigned offset=0,count=3;
    if(which==1) { offset=6;count=4; }
    if(which>=2) {
        int fct=which==3;
        model_write_u32(s,0x3c8,fct?0xd324:0xd328);
        s[0x3c4]=fct?5:3;
        offset=14;count=fct?12:5;
    }
    /* Original logs task submission failure but still returns success. */
    e->call(e->ctx,0x7554,0,count,0,0,boot_tasks+offset,count*8);
    return 0;
}

static uint32_t power_off(uint8_t *s,const sg560d_environment *e,uint32_t force) {
    if(dep(e,0x76d8,0,0)) return 0;
    int32_t v18=(int32_t)dep(e,0x4c50,15,0);
    if(v18>1699 || force) {
        dep(e,0x5048,0,0);
        dep(e,0x4e34,0,0);
        if(dep(e,0x3150,0,0)) dep(e,0x4fd0,0,0);
        else { dep(e,0x4ee0,0,0);dep(e,0x4ed4,0,0); }
        set_mode(s,e,1);
        s[0x4f2]=3;
        model_write_u64(s,0x518,now(e)+3000);
    }
    dep(e,0x5e30,0,0);
    dep(e,0x6248,0,0);
    dep(e,0x7928,1,0);
    s[0x3cf]=s[0x4f8]=0;
    model_write_u64(s,0x4e8,0);
    return 1;
}

static uint32_t prepare_boot(uint8_t *s,const sg560d_environment *e,uint32_t mode) {
    if(mode==4) dep(e,0x8054,11,1);
    uint32_t success=(uint32_t)dep(e,0x5f30,0,0);
    if(!success) {
        dep(e,0x6248,0,0);dep(e,0x7928,1,0);
        if(mode==4) dep(e,0x8054,11,0);
    } else {
        set_mode(s,e,mode==0?s[0x3c4]:mode);
        if(mode==0) dep(e,0x364e,29,0);
        dep(e,0x8054,8,1);
        if(mode==0) model_write_u32(s,0x454,(uint32_t)now(e));
    }
    return success;
}

static uint32_t discover_power(uint8_t *s,const sg560d_environment *e,uint32_t mode) {
    dep(e,0x6282,0,0);
    if((int32_t)dep(e,0x4c50,15,0)>1699) {
        if(mode<2) mode=2;
        s[0x4f2]=s[0x4f1]=2;
        model_write_u64(s,0x4e0,now(e));
    } else { mode=1;s[0x4f2]=s[0x4f1]=0; }
    set_mode(s,e,mode);
    if(s[0x4f1]==2) {
        dep(e,0x614c,0,0);dep(e,0x7928,0,0);
        return 1;
    }
    dep(e,0x6248,0,0);dep(e,0x7928,1,0);
    if(dep(e,0x3150,0,0)) dep(e,0x4fd0,0,0);
    return 0;
}

/* Main power-monitor poll, 0x6a68. Keep dependency read order: some reads also
 * update the upstream power-monitor state. Diagnostic output alone is omitted. */
static void poll(uint8_t *s,const sg560d_environment *e) {
    dep(e,0x5694,0,0);
    int32_t v18=(int32_t)dep(e,0x4c50,15,0);
    if(v18>1699) dep(e,0x559c,0,0);
    if(model_read_u64(s,0x4e8) && now(e)>=model_read_u64(s,0x4e8)) {
        model_write_u64(s,0x4e8,0);s[0x4f8]=0;
        dep(e,0x4e34,1,0);dep(e,0x55b4,0,0);
    }
    if(v18>1699) {
        if(s[0x4f1]==0) {
            if(s[0x4f2]==1) {
                s[0x4f1]=s[0x4f2]=2;model_write_u64(s,0x518,0);
                dep(e,0x614c,0,0);
                dep(e,0x4c50,12,0);dep(e,0x4ca8,0,0);
                if(s[0x4f8]) model_write_u64(s,0x4e8,now(e)+50);
                dep(e,0x55b4,0,0);model_write_u64(s,0x4e0,now(e));
                if(model_read_u64(s,0x458)) model_write_u64(s,0x458,0);
                if(s[0x3cf]) {
                    s[0x3cf]=0;
                    dep(e,0x562c,0,0);dep(e,0x5670,0,0);
                    dep(e,0x55dc,0,0);s[0x508]=s[0x528]=0;
                    if(s[0x450]==5) {
                        uint32_t elapsed=(uint32_t)now(e)-model_read_u32(s,0x454);
                        if(elapsed) {
                            if(elapsed>14999) {
                                power_off(s,e,1);
                                const uint32_t retry[]={1,3000,0,0x65db};
                                e->call(e->ctx,0x7554,0,2,0,0,retry,sizeof(retry));
                            }
                            goto transition_done;
                        }
                    }
                    if(s[0x450]!=2) set_mode(s,e,2);
                }
            } else if(s[0x4f2]==0) {
                s[0x4f1]=s[0x4f2]=2;model_write_u64(s,0x518,0);
                dep(e,0x614c,0,0);dep(e,0x7928,0,0);set_mode(s,e,2);
            }
        }
    } else if(s[0x4f1]==2) {
        if(s[0x4f2]==3) {
            s[0x4f2]=s[0x4f1]=0;model_write_u64(s,0x518,0);
            dep(e,0x5e30,0,0);model_write_u64(s,0x4e0,0);
        } else if(s[0x4f2]==2) {
            dep(e,0x559c,0,0);
            uint32_t floor=(uint32_t)dep(e,0x55c4,0,0);
            dep(e,0x4c50,14,0);
            if(dep(e,0x562c,0,0)==0 && floor<=2499) dep(e,0x55dc,6,0);
            dep(e,0x562c,0,0);dep(e,0x5670,0,0);
            dep(e,0x55b4,0,0);
            uint32_t reason=(uint32_t)dep(e,0x567c,0,0);
            s[0x4f2]=s[0x3cf]=1;model_write_u64(s,0x4e0,0);s[0x4f1]=0;
            model_write_u64(s,0x518,now(e)+250);schedule_retry(s,e,reason);
        }
    }
transition_done:
    if(model_read_u64(s,0x518) && now(e)>model_read_u64(s,0x518)) {
        if(!s[0x3cf]) {
            if(s[0x4f1]==0 && s[0x4f2]==1) {
                uint8_t mode=s[0x450];power_off(s,e,1);
                if((uint32_t)(mode-3)>2) schedule_retry(s,e,(uint32_t)dep(e,0x567c,0,0));
            }
        } else if(s[0x4f1]==0 && s[0x4f2]==1) {
            s[0x3cf]=0;
            if(dep(e,0x567c,0,0)==1) power_on(s,e,0);
            else power_off(s,e,1);
        }
        s[0x4f2]=s[0x4f1];model_write_u64(s,0x518,0);
    }
    uint8_t rgb[3],bits[3];
    for(unsigned i=0;i<3;++i) bits[i]=dep(e,0x80f8,18+i,0)==1;
    for(unsigned i=0;i<3;++i) s[0x4f9+i]=(uint8_t)((s[0x4f9+i]<<1)|bits[i]);
    memcpy(rgb,s+0x3cc,3);
    for(unsigned i=0;i<3;++i) {
        if(s[0x4f9+i]==0) rgb[i]=0;
        else if((s[0x4f9+i]&7)==7) rgb[i]=1;
    }
    if(memcmp(rgb,s+0x3cc,3)) {
        model_write_u32(s,0x530,(uint32_t)now(e));
        if(!rgb[0] && rgb[1] && !rgb[2]) model_write_u32(s,0x52c,(uint32_t)now(e));
        if(!rgb[0] && !rgb[1] && !rgb[2]) (void)now(e);
        memcpy(s+0x3cc,rgb,3);
    }
    uint32_t green=0,cyan=0,yellow=0;
    if(rgb[1]) {
        green=rgb[1];
        if(!rgb[0]) {
            if(rgb[2]) { green=0;cyan=rgb[2]; }
        } else { green=0;yellow=rgb[2]^1; }
    }
    int stable=model_read_u32(s,0x530)!=0 && now(e)-(uint64_t)model_read_u32(s,0x530)>=1001;
    uint32_t theme=(uint32_t)dep(e,0x5dbc,0,0);
    if(stable) {
        uint32_t desired=green?5:cyan?6:yellow?7:0;
        if(desired && theme!=desired) dep(e,0x5c68,desired,0);
        model_write_u32(s,0x530,0);
    }
    dep(e,0x49d0,0x200000e0,0);
    int32_t usb=(int32_t)dep(e,0x4c50,16,0);
    int present=usb>4499;
    if(!s[0x50a]) { s[0x4f0]=(uint8_t)present;s[0x50a]=1; }
    uint8_t current=s[0x4f1],target=s[0x4f2];
    uint32_t automatic=(uint32_t)dep(e,0x3114,0,0);
    if(current==0 && target==0) {
        if(model_read_u64(s,0x458) && now(e)>=model_read_u64(s,0x458)) {
            int32_t temperature=(int32_t)dep(e,0x7d54,0,0);
            int32_t header=(int32_t)dep(e,0x4c50,13,0);
            uint32_t reason=(uint32_t)dep(e,0x562c,0,0);
            uint64_t age=dep(e,0x5638,0,0);
            int permitted=0;
            if(temperature<500) {
                if(reason==3) permitted=(usb>4499 || header>4499) && age>=backoff_base[reason];
                else if((uint8_t)(reason-3)<4 || reason==0) permitted=age>=backoff_base[reason];
                else permitted=1;
            }
            if(permitted) { model_write_u64(s,0x458,0);power_on(s,e,0); }
            else if(now(e)>=model_read_u64(s,0x510)) {
                model_write_u64(s,0x510,now(e)+60000);
                dep(e,0x5638,0,0);
            }
        }
        if(automatic && s[0x508] && !dep(e,0x517c,0,0)) {
            if(now(e)>=model_read_u64(s,0x500)) {
                int blocked=0;
                if(s[0x528]==3) {
                    int32_t header=(int32_t)dep(e,0x4c50,13,0);
                    blocked=usb<=4499 && header<=4499;
                }
                if(!blocked) {
                    uint8_t reason=s[0x528];
                    uint32_t attempts=model_read_u32(s,0x4f4)+1;model_write_u32(s,0x4f4,attempts);
                    uint32_t delay=retry_delay(e,reason,attempts);
                    model_write_u64(s,0x500,now(e)+delay);
                    power_on(s,e,0);s[0x528]=reason;s[0x508]=1;s[0x509]=0;
                }
            }
        }
    }
    if(s[0x508] && model_read_u64(s,0x4e0) && s[0x4f1]==2 && now(e)-model_read_u64(s,0x4e0)>119999) {
        model_write_u32(s,0x4f4,0);s[0x508]=s[0x528]=0;
    }
    uint32_t reason=(uint32_t)dep(e,0x567c,0,0);
    int owns=s[0x508] && s[0x528] ? s[0x508] : reason==2;
    if(!dep(e,0x517c,0,0) && current==0 && target==0 && automatic) {
        if(!owns) {
            if(!s[0x4f0] && present) { model_write_u64(s,0x520,now(e));s[0x509]=1;goto usb_done; }
            if(!s[0x509]) { if(present) goto usb_done; }
            else if(present) {
                if(now(e)-model_read_u64(s,0x520)>4999) { s[0x509]=0;power_on(s,e,0); }
                goto usb_done;
            }
        }
    }
    s[0x509]=0;
usb_done:
    s[0x4f0]=(uint8_t)present;
}

uint64_t sg560d_execute(uint8_t s[4096],const sg560d_environment *e,uint32_t entry,uint32_t a,uint32_t b) {
    switch(entry) {
    case 0x5e30:uart_stop(s,e);return 0;
    case 0x5f30:return power_check(s,e);
    case 0x614c:uart_start(s,e);return 0;
    case 0x61b8:return 1;
    case 0x61d0:dep(e,0x364e,29,1);return 1;
    case 0x61f0:dep(e,0x8054,11,0);return 1;
    case 0x6210:case 0x6230:case 0x6238:case 0x6240:dep(e,0x8054,8,0);return 1;
    case 0x6248:pins_off(e);return 0;
    case 0x6282:pins_on(s,e);return 0;
    case 0x62ec:return retry_delay(e,a,b);
    case 0x6384:schedule_retry(s,e,a);return 0;
    case 0x6428:return power_on(s,e,0);
    case 0x64a0:return power_on(s,e,1);
    case 0x6520:return power_on(s,e,a?3:2);
    case 0x65d0:return power_on(s,e,3);
    case 0x65da:power_on(s,e,3);return 1;
    case 0x65e4:return power_on(s,e,2);
    case 0x65f0:model_write_u64(s,0x458,a?now(e)+(uint64_t)a*1000:0);return 0;
    case 0x6650: {
        uint64_t time=now(e),target=model_read_u64(s,0x458);
        if(!target)return UINT32_MAX;
        return time>=target?0:(uint32_t)((target-time)/1000);
    }
    case 0x6690:return s[0x4f1]==0;
    case 0x66a0: {
        static const uint32_t names[5]={0xd5ba,0xd73c,0xd328,0xdba1,0xd324};
        unsigned index=(uint8_t)(a-1);return index<5?names[index]:0xcceb;
    }
    case 0x66bc:set_mode(s,e,a);return 0;
    case 0x6720:return power_off(s,e,a);
    case 0x6838:return prepare_boot(s,e,0);
    case 0x68a4:return prepare_boot(s,e,4);
    case 0x68fc:return prepare_boot(s,e,2);
    case 0x6948:return discover_power(s,e,a);
    case 0x6a28:dep(e,0x8054,8,1);return 0;
    case 0x6a48:dep(e,0x8054,8,0);return 0;
    case 0x6a68:poll(s,e);return 0;
    case 0x7468:dep(e,0x364e,(uint8_t)a,b);dep(e,0x77c0,250,0);dep(e,0x364e,(uint8_t)a,b^1);return 0;
    case 0x7488:sg560d_execute(s,e,0x7468,8,1);return 1;
    case 0x74a8:case 0x74c8:sg560d_execute(s,e,0x7468,39,0);return 1;
    default:return UINT64_MAX; /* Explicitly unsupported, not a simulated success. */
    }
}
