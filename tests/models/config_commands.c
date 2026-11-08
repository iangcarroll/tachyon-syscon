#include "syscon_config_commands.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <limits.h>

static void emit(syscon_config_commands *ctx, const char *format, ...) {
    char text[160];
    va_list args;
    va_start(args, format);
    vsnprintf(text, sizeof(text), format, args);
    va_end(args);
    ctx->print(ctx->print_context, text);
}

/* Exact conversion counts of the firmware's two fixed sscanf scanset formats.
 * A missing final literal colon does not undo a successful conversion. */
static unsigned scan(const char *args, char key[32], char value[32], unsigned wanted) {
    if (!args || !*args || *args == ':') return 0;
    unsigned i = 0;
    while (i < 31 && args[i] && args[i] != ':') { key[i] = args[i]; ++i; }
    key[i] = 0;
    if (wanted == 1 || args[i] != ':') return 1;
    args += i+1;
    if (!*args || *args == ':') return 1;
    i = 0;
    while (i < 31 && args[i] && args[i] != ':') { value[i] = args[i]; ++i; }
    value[i] = 0;
    return 2;
}

static void legacy_copy(char out[32], const uint8_t *in) {
    strncpy(out, (const char *)in, 32);
    out[30] = 0;
    char *semi = strchr(out, ';');
    if (semi) *semi = 0;
}

static int find(syscon_store *store, char key[32], char value[32]) {
    if (strlen(key) >= 31) return 0;
    long long parsed = strtoll(key, NULL, 10);
    int32_t index = parsed > INT32_MAX ? INT32_MAX : parsed < INT32_MIN ? INT32_MIN : (int32_t)parsed;
    if ((uint32_t)index >= store->count || !syscon_slot_valid(&store->slots[index])) return 0;
    legacy_copy(key, store->slots[index].key);
    legacy_copy(value, store->slots[index].value);
    return 1;
}

static int dump(syscon_config_commands *ctx, syscon_store *store) {
    unsigned rejected = 0;
    for (unsigned i = 0; i < store->count; ++i) {
        char key[32], value[32];
        snprintf(key, sizeof(key), "%u", i);
        if (find(store, key, value)) emit(ctx, "%s = %s", key, value);
        else {
            const uint8_t *slot = (const uint8_t *)&store->slots[i];
            unsigned j = 0;
            while (j < 64 && slot[j] == 0xff) ++j;
            if (j != 64) { emit(ctx, "slot %u REJECTED", i); ++rejected; }
        }
    }
    emit(ctx, "No more keys found");
    if (rejected) emit(ctx, "WARNING: %d rejected slot(s), re-set to replace", (int)rejected);
    return 1;
}

int syscon_config_dispatch(void *context, uint32_t handler, const char *arguments) {
    syscon_config_commands *ctx = context;
    if (handler == 0x3fdc) {
        static const char *keys[6] = {"sys.auto_boot", "sys.wake_pin_enable",
            "sys.color_debug_enable", "sys.fastboot_enabled", "sys.demo_enabled", "sys.enable_5v_when_off"};
        for (unsigned i = 0; i < 6; ++i)
            emit(ctx, "%s: %s", keys[i], ctx->runtime[i] ? "true" : "false");
        uint32_t edl = 0, shutdown = 0;
        for (unsigned i = 0; i < 4; ++i) {
            edl |= (uint32_t)ctx->runtime[6+i] << (8*i);
            shutdown |= (uint32_t)ctx->runtime[10+i] << (8*i);
        }
        emit(ctx, "sys.edl_timer: %d", (int32_t)edl);
        emit(ctx, "sys.shutdown_timer: %d", (int32_t)shutdown);
        return 1;
    }
    int identity = handler == 0x4490 || handler == 0x45e0 || handler == 0x45f8 ||
                   handler == 0x4638 || handler == 0x4684;
    syscon_store *store = identity ? ctx->identity : ctx->config;
    if (handler == 0x45e0 || handler == 0x45ec) return dump(ctx, store);
    int is_set = handler == 0x4684 || handler == 0x4760;
    int is_get = handler == 0x4638 || handler == 0x4714;
    int is_find = handler == 0x4490 || handler == 0x44dc;
    int is_erase = handler == 0x45f8 || handler == 0x46d4;
    if (!is_set && !is_get && !is_find && !is_erase) return -2;
    char key[32], value[32];
    if (scan(arguments, key, value, is_set ? 2 : 1) != (unsigned)(is_set ? 2 : 1)) {
        emit(ctx, "Invalid parameters. Use \"HELP:;\" for more details.");
        return 0;
    }
    int result;
    if (is_set) {
        char previous[32];
        int unchanged = !identity && syscon_store_get(store, key, previous) == 1 && strcmp(previous, value) == 0;
        result = identity ? syscon_store_append(store, key, value) : syscon_config_set(store, key, value);
        if (result < 0) return result;
        if (result) {
            if (!unchanged) syscon_config_load(ctx->config, ctx->identity, ctx->runtime);
            emit(ctx, "%s = %s", key, value);
        } else emit(ctx, "Refused: %s", key);
    } else if (is_get || is_find) {
        result = is_get ? syscon_store_get(store, key, value) : find(store, key, value);
        if (result < 0) return result;
        if (result) emit(ctx, is_find ? "Found: %s = %s" : "%s = %s", key, value);
        else emit(ctx, "Not found: %s", key);
    } else {
        result = 0;
        if (strcmp(key, identity ? "B23000" : "particle") == 0 && syscon_store_erase(store)) {
            result = syscon_store_append(store, "confVersion", "1");
            if (syscon_store_get(store, "confVersion", value) != 1) {
                if (store->io.fault) store->io.fault(store->io.context);
                return -1;
            }
            if (!identity) syscon_config_load(ctx->config, ctx->identity, ctx->runtime);
        }
        emit(ctx, result ? (identity ? "CONFIG_ID_ERASE erased" : "Erased") : "Invalid password");
    }
    return result;
}
