#include "format.h"
typedef struct {
    uint8_t *out;uint32_t cap,used,args;int okay;
    const syscon_format_memory *memory;
    syscon_format_target_output target;
    syscon_format_call call;void *call_context;
} output;
static uint8_t byte(output *o,uint32_t address) {
    if(!o->memory)return *(const volatile uint8_t *)(uintptr_t)address;
    uint8_t v=0;
    if(!o->memory->read_byte(o->memory->ctx,address,&v))o->okay=0;
    return v;
}
static uint32_t word(output *o,uint32_t address) {
    if(!o->memory)return *(const volatile uint32_t *)(uintptr_t)address;
    uint32_t v=0;
    for(unsigned i=0;i<4 && o->okay;i++)v|=(uint32_t)byte(o,address+i)<<(i*8);
    return v;
}
static uint32_t argument(output *o) { uint32_t v=word(o,o->args);o->args+=4;return v; }
static uint64_t long_argument(output *o) {
    o->args=(o->args+7u)&~7u;
    uint64_t lo=argument(o);return lo|((uint64_t)argument(o)<<32);
}
static void emit(output *o,uint8_t c) {
    if(!o->okay)return;
    if(o->out && o->used<o->cap)o->out[o->used]=c;
    o->used++;
    if(o->call)syscon_format_forward(&o->target,c,o->call,o->call_context);
}
void syscon_format_forward(syscon_format_target_output *output,uint32_t character,
                           syscon_format_call call,void *context) {
    output->count++;
    call(context,output->callback,character,output->context);
}
static void number(output *o,uint64_t n,unsigned radix,int upper) {
    uint8_t digits[24];unsigned count=0;
    do{
        unsigned digit=(unsigned)(n%radix);n/=radix;
        digits[count++]=(uint8_t)(digit<10?'0'+digit:(upper?'A':'a')+digit-10);
    }while(n);
    while(count)emit(o,digits[--count]);
}
static syscon_format_result format_impl(uint8_t *out,uint32_t cap,uint32_t format,uint32_t arguments,
    const syscon_format_memory *memory,uint32_t callback,uint32_t context,
    syscon_format_call call,void *call_context) {
    output o={out,cap,0,arguments,1,memory,{callback,context,0},call,call_context};
    while(o.okay) {
        uint8_t c=byte(&o,format);
        if(!c || !o.okay)break;
        if(c!='%'){emit(&o,c);format++;continue;}
        uint32_t p=format+1;uint8_t sign=0;int alternate=0;
        while(o.okay){
            c=byte(&o,p);
            if(c=='#')alternate=1;
            else if(c=='+')sign='+';
            else if(c==' '){if(!sign)sign=' ';}
            else break;
            p++;
        }
        unsigned length=0;
        if(c=='h'){length=1;p++;if(byte(&o,p)=='h'){length=3;p++;}}
        else if(c=='l'){length=4;p++;if(byte(&o,p)=='l'){length=5;p++;}}
        else if(c=='j'){length=6;p++;}
        else if(c=='z'){length=7;p++;}
        else if(c=='t'){length=8;p++;}
        c=byte(&o,p);
        if(c!='%' && c!='c' && c!='s' && c!='d' && c!='i' && c!='u' && c!='o' && c!='x' && c!='X' && c!='p') {
            emit(&o,'%');format++;continue;
        }
        format=p+1;
        if(c=='%'){emit(&o,'%');continue;}
        if(c=='c'){emit(&o,(uint8_t)argument(&o));continue;}
        if(c=='s'){
            uint32_t address=argument(&o);
            /* Original computes strlen before the first callback, then rereads
             * exactly that many bytes. A callback may modify the source. */
            uint32_t length=0;
            while(o.okay && byte(&o,address+length))length++;
            for(uint32_t i=0;i<length && o.okay;i++)emit(&o,byte(&o,address+i));
            continue;
        }
        if(c=='p'){uint32_t n=argument(&o);emit(&o,'0');emit(&o,'x');number(&o,n,16,0);continue;}
        uint64_t n;
        if(length==5 || length==6)n=long_argument(&o);
        else{
            uint32_t v=argument(&o);
            if(length==3)v&=255;
            else if(length==1)v&=65535;
            n=v;
            if(c=='d' || c=='i'){
                /* Original %hhd zero-extends, despite the signed conversion. */
                if(length==1)n=(uint64_t)(int64_t)(int16_t)v;
                else if(length!=3)n=(uint64_t)(int64_t)(int32_t)v;
            }
        }
        if(c=='d' || c=='i'){
            if(n>>63){sign='-';n=0-n;}
            if(sign)emit(&o,sign);
            number(&o,n,10,0);
        }else{
            unsigned radix=c=='o'?8:(c=='u'?10:16);
            if(n && alternate){
                if(radix==8)emit(&o,'0');
                if(radix==16){emit(&o,'0');emit(&o,c);}
            }
            number(&o,n,radix,c=='X');
        }
    }
    if(out && cap){if(o.used<cap)out[o.used]=0;out[cap-1]=0;}
    syscon_format_result result={o.used,o.args,o.okay};return result;
}
syscon_format_result syscon_vformat(uint8_t *out,uint32_t cap,uint32_t format,uint32_t arguments,
                                   const syscon_format_memory *memory) {
    return format_impl(out,cap,format,arguments,memory,0,0,0,0);
}
syscon_format_result syscon_vformat_callback(uint32_t callback,uint32_t context,syscon_format_call call,
    void *call_context,uint32_t format,uint32_t arguments,const syscon_format_memory *memory) {
    if(!call){syscon_format_result result={0,arguments,0};return result;}
    return format_impl(0,0,format,arguments,memory,callback,context,call,call_context);
}

/* Original target loads variadic words atomically with a 32-bit LDR. A byte
 * callback adapter cannot preserve access widths or boundary fault addresses. */
syscon_format_result syscon_vformat_target(uint8_t *out,uint32_t cap,uint32_t format,uint32_t arguments) {
    return format_impl(out,cap,format,arguments,0,0,0,0,0);
}
