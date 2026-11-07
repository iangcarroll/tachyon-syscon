/* Minimal memory routines for the isolated ARM test ELF; no host libc calls. */
#include <stddef.h>
#include <stdint.h>

/* Compiler support newly required by the rebuilt logging C. There is no
 * separately identified counterpart in the pinned image; this is not counted
 * as another reconstructed original function. Use only 32-bit shifts so it
 * cannot recursively call the helper being implemented. */
uint64_t __aeabi_llsr(uint64_t value,unsigned shift) {
    union {uint64_t wide;struct {uint32_t low,high;} word;} v={value};
    if(shift>=64){v.word.low=0;v.word.high=0;}
    else if(shift>=32){v.word.low=v.word.high>>(shift-32);v.word.high=0;}
    else if(shift){v.word.low=(v.word.low>>shift)|(v.word.high<<(32-shift));v.word.high>>=shift;}
    return v.wide;
}

void *memcpy(void *destination,const void *source,size_t count) {
    unsigned char *out=destination;
    const unsigned char *in=source;
    for(size_t i=0;i<count;++i)out[i]=in[i];
    return destination;
}
void *memset(void *destination,int value,size_t count) {
    unsigned char *out=destination;
    for(size_t i=0;i<count;++i)out[i]=(unsigned char)value;
    return destination;
}
int memcmp(const void *left,const void *right,size_t count) {
    const unsigned char *a=left,*b=right;
    for(size_t i=0;i<count;++i)if(a[i]!=b[i])return (int)a[i]-(int)b[i];
    return 0;
}
