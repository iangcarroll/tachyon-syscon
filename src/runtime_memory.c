#include "runtime_memory.h"
int syscon_rt_strcmp(const void *left,const void *right) {
    const uint8_t *a=left,*b=right;
    while(*a && *a==*b){++a;++b;}
    return (int)*a-(int)*b;
}
uint32_t syscon_rt_strlen(const void *text) {
    const uint8_t *s=text;uint32_t n=0;
    while(s[n])++n;
    return n;
}
int syscon_rt_memcmp(const void *left,const void *right,uint32_t size) {
    const uint8_t *a=left,*b=right;
    for(uint32_t i=0;i<size;++i)if(a[i]!=b[i])return (int)a[i]-(int)b[i];
    return 0;
}
void *syscon_rt_memcpy(void *destination,const void *source,uint32_t size) {
    uint8_t *out=destination;const uint8_t *in=source;
    for(uint32_t i=0;i<size;++i)out[i]=in[i];
    return destination;
}
void *syscon_rt_memset(void *destination,int value,uint32_t size) {
    uint8_t *out=destination;
    for(uint32_t i=0;i<size;++i)out[i]=(uint8_t)value;
    return destination;
}
void *syscon_rt_strchr(const void *text,int value) {
    const uint8_t *s=text;uint8_t c=(uint8_t)value;
    while(*s && *s!=c)++s;
    return *s==c ? (void *)s : 0;
}
int syscon_rt_strncmp(const void *left,const void *right,uint32_t size) {
    const uint8_t *a=left,*b=right;
    for(uint32_t i=0;i<size;++i){
        if(a[i]!=b[i] || !a[i])return (int)a[i]-(int)b[i];
    }
    return 0;
}
void *syscon_rt_strncpy(void *destination,const void *source,uint32_t size) {
    uint8_t *out=destination;const uint8_t *in=source;uint32_t i=0;
    for(;i<size;++i){out[i]=in[i];if(!in[i]){++i;break;}}
    for(;i<size;++i)out[i]=0;
    return destination;
}
void *syscon_rt_strrchr(const void *text,int value) {
    if(!value)return syscon_rt_strchr(text,0);
    void *last=0,*next;const uint8_t *s=text;
    while((next=syscon_rt_strchr(s,value))!=0){last=next;s=(const uint8_t *)next+1;}
    return last;
}
void *syscon_rt_memchr(const void *data,int value,uint32_t size) {
    const uint8_t *s=data;
    for(uint32_t i=0;i<size;++i)if(s[i]==(uint8_t)value)return (void *)(s+i);
    return 0;
}
