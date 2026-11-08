/* Three retained bytes held in SYSCTL GENERAL.SCRATCHPAD[0..2]. */
#include "timers.h"

void syscon_retained_commit(const syscon_retained *s, syscon_register_write write, void *ctx) {
    /* Original snapshots all three bytes on its stack before the first write. */
    const syscon_retained snapshot=*s;
    write(ctx,0x400b0400,snapshot.magic);
    write(ctx,0x400b0404,snapshot.modes);
    write(ctx,0x400b0408,snapshot.boots);
}

void syscon_retained_clear_registers(syscon_register_write write, void *ctx) {
    /* Deliberately does not modify the in-RAM copy, matching 0x5a88. */
    write(ctx,0x400b0400,0);
    write(ctx,0x400b0404,0);
    write(ctx,0x400b0408,0);
}

void syscon_retained_load(syscon_retained *s, syscon_register_read read,
                          syscon_register_write write, void *ctx) {
    const uint8_t magic=(uint8_t)read(ctx,0x400b0400);
    const uint8_t modes=(uint8_t)read(ctx,0x400b0404);
    const uint8_t boots=(uint8_t)read(ctx,0x400b0408);
    s->magic=magic;
    s->modes=modes;
    s->boots=boots;
    if(s->magic!=0x5b) {
        s->magic=0x5b;
        s->modes=s->boots=0;
        syscon_retained_commit(s,write,ctx);
    }
}

void syscon_retained_set_modem(syscon_retained *s, uint8_t value, syscon_register_write write, void *ctx) {
    s->modes=(s->modes&0xf0)|(value&0x0f);
    syscon_retained_commit(s,write,ctx);
}

void syscon_retained_set_battery(syscon_retained *s, uint8_t value, syscon_register_write write, void *ctx) {
    s->modes=(s->modes&0x0f)|(uint8_t)(value<<4);
    syscon_retained_commit(s,write,ctx);
}

void syscon_retained_increment_boots(syscon_retained *s, syscon_register_write write, void *ctx) {
    if(s->boots!=255) ++s->boots;
    syscon_retained_commit(s,write,ctx);
}

uint8_t syscon_retained_modem(const syscon_retained *s) { return s->modes&0x0f; }
uint8_t syscon_retained_battery(const syscon_retained *s) { return s->modes>>4; }
uint8_t syscon_retained_boots(const syscon_retained *s) { return s->boots; }
