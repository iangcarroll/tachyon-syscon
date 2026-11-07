#include <stdint.h>
#define E ((volatile uint32_t *)(uintptr_t)0x21008000)
static uint32_t sink(uint32_t character,uint32_t context,int mutate){
    uint32_t index=E[0]++;E[32+2*index]=character;E[33+2*index]=context;
    if(mutate && E[1]==1){volatile uint32_t *p=(volatile uint32_t *)(uintptr_t)context;p[0]=E[3];p[1]=0xabcdef01;p[2]+=7;}
    if(E[1]==2 && index==0){volatile uint8_t *p=(volatile uint8_t *)(uintptr_t)E[4];p[1]=0;p[2]='X';p[5]='!';p[6]=0;}
    if(E[1]==3 && index==0){volatile uint8_t *p=(volatile uint8_t *)(uintptr_t)E[4];p[1]='%';p[2]='x';*(volatile uint32_t *)(uintptr_t)E[5]=0x1234abcd;}
    return E[2];
}
uint32_t fixture_char_sink(uint32_t character,uint32_t context){return sink(character,context,1);}
uint32_t fixture_char_alternate(uint32_t character,uint32_t context){return sink(character,context,0);}
