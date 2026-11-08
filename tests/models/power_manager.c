#include "model_memory.h"
#include "power_manager.h"
#include <string.h>
#include <setjmp.h>
typedef struct { const syscon_power_environment *original;jmp_buf boundary; } power_guard;
static uint64_t guarded_call(void *ctx,uint32_t entry,uint32_t a,uint32_t b,const void *payload,uint32_t size) {
    power_guard *guard=ctx;
    uint64_t result=guard->original->call(guard->original->ctx,entry,a,b,payload,size);
    if((entry==0x3620 || entry==0x364e) && result==SYSCON_POWER_IO_TERMINATED)
        longjmp(guard->boundary,1);
    return result;
}
static uint64_t dep(const syscon_power_environment *e,uint32_t f,uint32_t a,uint32_t b) {
    return e->call(e->ctx,f,a,b,0,0);
}
static uint32_t get(const syscon_power_environment *e,uint32_t pin) { return (uint32_t)dep(e,0x3620,pin,0); }
static int32_t put(const syscon_power_environment *e,uint32_t pin,uint32_t value) { return (int32_t)dep(e,0x364e,pin,value); }
static uint32_t fail(const syscon_power_environment *e,uint32_t line,int *failed) {
    *failed=1;dep(e,0x2678,line,0);return 0;
}
static uint32_t selector(const syscon_power_environment *e,uint32_t first,uint32_t second,uint32_t line,int *failed) {
    uint32_t a=get(e,first),b=get(e,second);
    if (a==0 && b==1) return 2;
    if (a<=1 && b==0) return a;
    return fail(e,line,failed);
}
static uint32_t run(uint8_t *s,const syscon_power_environment *e,uint32_t entry,uint32_t a,int *failed) {
    uint32_t old,value;
    switch(entry) {
    case 0x4c50: {
        uint32_t sample=(uint32_t)dep(e,0x7f24,(uint16_t)a,0);
        if (!sample) sample=(uint32_t)dep(e,0x7f24,(uint16_t)a,0);
        uint32_t scale=0;
        if (a>=12 && a<=14) scale=3;
        if (a==15) scale=2;
        if (a==16) scale=8;
        if (a==23) scale=1;
        return sample*scale;
    }
    case 0x4ca8:return selector(e,33,34,0x131,failed);
    case 0x4d00:return selector(e,35,26,0x17c,failed);
    case 0x4d9c:return selector(e,40,25,0x1a2,failed);
    case 0x4d58:return get(e,38)!=0;
    case 0x4df4:return get(e,36)!=0;
    case 0x4ec4:return get(e,37)!=0;
    case 0x4d68:put(e,38,a!=0);return 0;
    case 0x4e04:put(e,36,a!=0);return 0;
    case 0x4ed4:put(e,37,a);return 0;
    case 0x5264:put(e,27,a!=0);return 0;
    case 0x4e34:
        if(a>2){*failed=1;return 0;}
        old=run(s,e,0x4ca8,0,failed);if(*failed)return 0;
        if(old==a)return 0;
        if(old){put(e,33,0);put(e,34,0);}
        if(a==1){run(s,e,0x4e04,0,failed);run(s,e,0x4d68,0,failed);put(e,33,1);}
        else if(a==2){run(s,e,0x4e04,1,failed);run(s,e,0x4d68,1,failed);put(e,34,1);}
        else run(s,e,0x4e04,1,failed);
        return 0;
    case 0x4ee0:
        if(a>2){*failed=1;return 0;}
        run(s,e,0x4ed4,1,failed);dep(e,0x77c0,20,0);
        run(s,e,0x4c50,13,failed);
        if(a==1){put(e,25,0);put(e,40,1);}
        else if(a==2){put(e,40,0);put(e,25,1);}
        else{dep(e,0x77c0,20,0);put(e,25,0);put(e,40,0);}
        value=run(s,e,0x4d9c,0,failed);if(*failed)return 0;
        if(value!=a){run(s,e,0x4d9c,0,failed);if(*failed)return 0;}
        value=run(s,e,0x4d9c,0,failed);if(*failed)return 0;
        if(value!=a)return fail(e,0x1e6,failed);
        return 0;
    case 0x4fd0:
        value=run(s,e,0x4d9c,0,failed);if(*failed)return 0;
        return value==1?0:run(s,e,0x4ee0,2,failed);
    case 0x5004: {
        uint32_t first=(uint32_t)put(e,32,a!=0);
        uint32_t second=(uint32_t)put(e,28,a==0);
        return first+second;
    }
    case 0x5048:
        if(a>2){*failed=1;return 0;}
        old=run(s,e,0x4d00,0,failed);if(*failed)return 0;
        if(old==a)return 0;
        if(a<2){put(e,35,a);put(e,26,0);run(s,e,0x5004,0,failed);}
        else{put(e,26,1);put(e,35,0);run(s,e,0x5004,1,failed);}
        value=run(s,e,0x4d00,0,failed);if(*failed)return 0;
        if(value!=a)return fail(e,0x168,failed);
        return 0;
    case 0x50f4:
        run(s,e,0x5004,0,failed);model_write_u64(s,0x378,dep(e,0x77b4,0,0));s[0x370]=0;return 1;
    case 0x5148:run(s,e,0x5004,1,failed);return 1;
    case 0x517c:
        if(s[0x370])return s[0x370];
        return model_read_u64(s,0x378) && (uint64_t)(dep(e,0x77b4,0,0)-model_read_u64(s,0x378))<2000;
    case 0x51c0: {
        if(run(s,e,0x517c,0,failed))return UINT32_MAX;
        if((int32_t)run(s,e,0x4c50,16,failed)<=4499)return UINT32_MAX;
        if(!run(s,e,0x4ec4,0,failed))return UINT32_MAX;
        static const uint32_t actions[]={0,0x5149,1,250,0,0x50f5};
        s[0x370]=1;model_write_u64(s,0x378,0);
        if((int32_t)e->call(e->ctx,0x7554,0,3,actions,sizeof(actions))<0){s[0x370]=0;return UINT32_MAX;}
        return 0;
    }
    case 0x5274:
        if((int32_t)run(s,e,0x4c50,14,failed)>2999)value=1;
        else{
            run(s,e,0x4e34,2,failed);if(*failed)return 0;
            run(s,e,0x4e04,1,failed);run(s,e,0x5264,0,failed);
            value=run(s,e,0x4c50,23,failed);
            run(s,e,0x4e34,0,failed);if(*failed)return 0;
            run(s,e,0x5264,1,failed);
            value=((uint32_t)(value-400u)>800u)+1;
        }
        dep(e,0x5ad4,value,0);run(s,e,0x4e04,0,failed);return value;
    default:*failed=1;return 0;
    }
}
uint64_t syscon_power_execute(uint8_t *s,const syscon_power_environment *e,uint32_t entry,uint32_t a) {
    power_guard guard={.original=e};
    if(setjmp(guard.boundary))return UINT64_MAX;
    syscon_power_environment checked={guarded_call,&guard};
    int failed=0;uint32_t result=run(s,&checked,entry,a,&failed);
    return failed?UINT64_MAX:result;
}
