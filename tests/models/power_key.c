#include "power_key.h"

void syscon_key_edge(syscon_power_key *s,uint32_t pin,syscon_key_call call,void *ctx) {
    call(ctx,0x80f8,pin,0,0,0);
    call(ctx,0x7880,0x5741,0,0,0);
    s->pin=(uint16_t)pin;
    call(ctx,0x81f8,0,0,0,0);
    call(ctx,0x781c,10,1,0x5845,0);
}

void syscon_key_debounce(syscon_power_key *s,syscon_key_call call,void *ctx) {
    uint32_t high=call(ctx,0x80f8,s->pin,0,0,0);
    int rearm;
    if (!s->mode) {
        if (high) call(ctx,0x6a48,0,0,0,0);
        else call(ctx,0x6a28,0,0,0,0);
    }
    if (high) {
        rearm=1;
        if (s->event==255) {
            call(ctx,0x8148,0,0,0x570d,0);
            return;
        }
    } else {
        rearm=!s->mode;
        if (s->event==255) {
            s->release_pending=0;
            s->pressed_ms=0;
            s->released_ms=0;
            s->forced=0;
            uint32_t active=call(ctx,0x6690,0,0,0,0);
            uint32_t ms=call(ctx,active ? 0x315c:0x3178,0,0,0,0)*1000u;
            s->ranges[0].end_ms=ms;
            s->ranges[1].start_ms=ms;
            s->ranges[1].end_ms=ms+5000u;
            s->ranges[2].start_ms=ms+5000u;
        }
    }
    call(ctx,0x781c,10,0,0x5741,0);
    if (rearm) call(ctx,0x8148,0,0,0x570d,0);
}

void syscon_key_poll(syscon_power_key *s,syscon_key_call call,void *ctx) {
    uint8_t old=s->event;
    if (!call(ctx,0x80f8,0,0,0,0)) {
        s->pressed_ms+=10u;
        s->released_ms=0;
        if (!s->mode && !s->forced && s->pressed_ms>5999u) {
            call(ctx,0x6a48,0,0,0,0);
            s->forced=1;
        }
    } else {
        s->release_pending=1;
        s->released_ms+=10u;
        s->pressed_ms=0;
    }
    for (unsigned i=0;i<3;i++) {
        if (s->pressed_ms>=s->ranges[i].start_ms && s->pressed_ms<s->ranges[i].end_ms) {
            s->event=(uint8_t)s->ranges[i].event;
            break;
        }
    }
    uint8_t finished=s->release_pending;
    if (finished) {
        if (s->released_ms<=200u) finished=0;
        else s->event++;
    }
    if (old!=s->event && s->callback)
        call(ctx,s->callback,s->event,s->user,0,0);
    if (finished) {
        s->release_pending=0;
        s->event=255;
        call(ctx,0x7880,0x5741,0,0,0);
        call(ctx,0x8148,0,0,0x570d,0);
    }
}

int syscon_key_register(syscon_power_key *s,uint32_t callback,uint32_t user) {
    s->callback=callback;s->user=user;return 0;
}

void syscon_key_mode(syscon_power_key *s,uint32_t mode,syscon_key_call call,void *ctx) {
    s->mode=(uint8_t)mode;
    call(ctx,0x8f88,3,0xcda6,0xcd8b,mode ? 0xcd84:0xcd7b);
    call(ctx,0x7880,0x5741,0,0,0);
    call(ctx,0x8148,0,0,0x570d,0);
    s->event=255;
}

int syscon_key_init(syscon_power_key *s,uint32_t mode,syscon_key_call call,syscon_key_configure configure,void *ctx) {
    uint8_t configuration[12]={0};configuration[5]=1;
    configure(ctx,0,configuration);
    syscon_key_mode(s,mode,call,ctx);
    call(ctx,0x776c,0,0,0,0);
    return 0;
}
