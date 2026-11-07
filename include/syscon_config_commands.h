#ifndef SYSCON_CONFIG_COMMANDS_H
#define SYSCON_CONFIG_COMMANDS_H
#include "syscon.h"

typedef struct {
    syscon_store *config, *identity;
    uint8_t runtime[22];
    syscon_print print;
    void *print_context;
} syscon_config_commands;

/* Implements the CONFIG/CONFIG_ID get/set/find/dump/erase and INTERNAL handlers.
 * Suitable for syscon_parser_feed's dispatch callback for those commands only.
 * Unsupported handlers return -2 and must not be routed here by a full firmware. */
int syscon_config_dispatch(void *context, uint32_t handler, const char *arguments);
#endif
