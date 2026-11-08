#include "syscon.h"
#include <string.h>

static unsigned lower(unsigned c) {
    return c >= 'A' && c <= 'Z' ? c + ('a'-'A') : c;
}
static unsigned upper(unsigned c) {
    return c >= 'a' && c <= 'z' ? c - ('a'-'A') : c;
}
static int prefix_equal(const char *a, const char *b) {
    while (*b) {
        if (lower((uint8_t)*a++) != lower((uint8_t)*b++)) return 0;
    }
    return 1;
}
static void failure(syscon_print print, void *ctx, const char *command, const char *why) {
    if (command) print(ctx, command);
    print(ctx, why);
    print(ctx, "FAIL");
}

void syscon_parser_init(syscon_parser *p, int enabled, int echo) {
    memset(p, 0, sizeof(*p));
    p->enabled = !!enabled;
    p->echo = !!echo;
}

void syscon_parser_feed(syscon_parser *p, const uint8_t *data, size_t len,
                        syscon_dispatch dispatch, syscon_print print,
                        syscon_echo echo, void *ctx) {
    char *buf = (char *)p->storage + 1;
    for (size_t i=0; i<len; ++i) {
        unsigned c = data[i];
        if (!p->enabled || c < 10 || c > 126) continue;
        if (p->echo && echo) echo(ctx, (uint8_t)c);
        if (p->used >= 125) {
            buf[127] = 0;
            failure(print, ctx, buf, "Buffer overflow");
            p->used = 0;
            continue; /* Original discards the byte which triggered overflow. */
        }
        if (c != '\r' && c != '\n') {
            buf[p->used++] = (char)c;
            continue;
        }
        if (!p->used) continue;
        buf[p->used] = 0;
        for (uint32_t j=0; j<p->used; ++j) if (buf[j] == ' ') buf[j] = ':';
        /* Keep original suffix and prefix matching quirks for ABI fidelity. */
        if (buf[p->used-1] != ';' || p->storage[p->used-1] != ':') {
            buf[p->used] = ':';
            buf[p->used+1] = ';';
            buf[p->used+2] = 0;
        }
        char *args = strchr(buf, ':');
        if (args) {
            ++args;
            if (!strchr(args, ':')) args = NULL;
        }
        unsigned j;
        for (j=0; j<37; ++j) if (prefix_equal(buf, syscon_commands[j].name)) break;
        if (j == 37) failure(print, ctx, buf, "Unknown command");
        else {
            const syscon_command *cmd = &syscon_commands[j];
            if (cmd->argument_policy == 1 && !args)
                failure(print, ctx, buf, "Parameters required");
            else if (cmd->argument_policy == 0 && args)
                failure(print, ctx, buf, "No parameters required");
            else {
                char uppercase[128];
                if (args && cmd->uppercase_arguments) {
                    size_t n=strlen(args);
                    if (n>127) n=127;
                    memcpy(uppercase,args,n);
                    uppercase[n]=0;
                    for (size_t k=0;k<n;k++) uppercase[k]=(char)upper((uint8_t)uppercase[k]);
                    args=uppercase;
                }
                int result=dispatch(ctx,cmd->original_handler,args);
                print(ctx,result ? "PASS" : "FAIL");
            }
        }
        p->used=0;
    }
}
