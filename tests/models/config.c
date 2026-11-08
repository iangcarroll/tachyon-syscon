/* Reconstructed from syscon 1.0.52. Peripheral operations are explicit callbacks;
 * no target flash controller is driven by this host-side compatibility model. */
#include "syscon.h"
#include <string.h>
#include <stdlib.h>
#include <limits.h>

uint8_t syscon_checksum31(const uint8_t field[31]) {
    uint8_t checksum = 0;
    for (unsigned i = 0; i < 31; ++i) checksum ^= field[i];
    return checksum;
}

int syscon_field_readable(const uint8_t field[31]) {
    for (unsigned i = 0; i < 31; ++i) {
        uint8_t c = field[i];
        if (c == 0 || c == ';') return 1;
        if (!((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
              (c >= '0' && c <= '9') || c == '_' || c == '-' || c == '.')) return 0;
    }
    return 0;
}

int syscon_field_writable(const uint8_t *field) {
    /* The original calls strchr over the whole NUL-terminated input after its
     * bounded validation. Callers must supply a terminated string. */
    return syscon_field_readable(field) && strchr((const char *)field, ';') == NULL;
}

int syscon_slot_valid(const syscon_slot *slot) {
    return syscon_field_readable(slot->key) && syscon_field_readable(slot->value) &&
           syscon_checksum31(slot->key) == slot->key_checksum &&
           syscon_checksum31(slot->value) == slot->value_checksum;
}

int syscon_slot_encode(syscon_slot *slot, const char *key, const char *value) {
    size_t k = strlen(key), v = strlen(value);
    if (k >= 31 || v >= 31 || !syscon_field_writable((const uint8_t *)key) ||
        !syscon_field_writable((const uint8_t *)value)) return 0;
    memset(slot, 0xff, sizeof(*slot));
    memcpy(slot->key, key, k+1);
    memcpy(slot->value, value, v+1);
    slot->key_checksum = syscon_checksum31(slot->key);
    slot->value_checksum = syscon_checksum31(slot->value);
    return 1;
}

int syscon_find_legacy(const syscon_slot *slots, size_t count, const char *key) {
    size_t len = strlen(key);
    if (!len || len >= 31) return -1;
    while (count) {
        --count;
        /* Original 0x29a0 calls validation but ignores its return in mode 1.
         * Preserve this in the compatibility layer, do not silently "repair". */
        if (memcmp(slots[count].key, key, len+1) == 0) return (int)count;
    }
    return -1;
}

static int store_fault(syscon_store *store) {
    if (store->io.fault) store->io.fault(store->io.context);
    return -1; /* In firmware the assertion handler resets, and never returns. */
}

int syscon_store_get(syscon_store *store, const char *key, char value[32]) {
    if (strlen(key) >= 31) return 0;
    if (!key[0]) return store_fault(store);
    int slot = syscon_find_legacy(store->slots, store->count, key);
    if (slot < 0) return 0;
    strncpy(value, (const char *)store->slots[slot].value, 32);
    value[30] = 0;
    char *end = strchr(value, ';');
    if (end) *end = 0;
    return 1;
}

static int first_blank(const syscon_store *store) {
    for (size_t i = 0; i < store->count; ++i) {
        const uint8_t *bytes = (const uint8_t *)&store->slots[i];
        size_t n = 0;
        while (n < 64 && bytes[n] == 0xff) ++n;
        if (n == 64) return (int)i;
    }
    return -1;
}

static void copy_field(uint8_t out[31], const char *in) {
    size_t n = strlen(in);
    if (n > 30) n = 30;
    memcpy(out, in, n);
    out[n] = 0;
}

/* 0x28d4: validation calls are diagnostic only. In particular, compaction may
 * preserve legacy values containing semicolons or otherwise invalid characters.
 * '%' invokes the original snprintf with missing variadic arguments. Refuse to
 * invent host-dependent output: -2 marks this unimplemented corruption case. */
static int write_slot(syscon_store *store, unsigned index, const char *key, const char *value) {
    size_t offset = (size_t)index * 64;
    if (store->io.blank(store->io.context, offset) != 3) return 0;
    if (strchr(key, '%') || strchr(value, '%')) return -2;
    syscon_slot slot;
    memset(&slot, 0xff, sizeof(slot));
    copy_field(slot.key, key);
    copy_field(slot.value, value);
    slot.key_checksum = syscon_checksum31(slot.key);
    slot.value_checksum = syscon_checksum31(slot.value);
    for (size_t i = 0; i < 64; i += 8) {
        if (store->io.program(store->io.context, offset+i, (const uint8_t *)&slot+i) != 3)
            return 0;
    }
    return 1;
}

int syscon_store_erase(syscon_store *store) {
    /* 0x27a8 requests a sector erase at each slot address. The peripheral, not
     * this loop, determines sector geometry; the MSPM0 model uses 1024 bytes. */
    for (size_t offset = 0; offset < store->count * 64; offset += 64)
        if (store->io.erase(store->io.context, offset) != 3) return 0;
    return 1;
}

int syscon_store_append(syscon_store *store, const char *key, const char *value) {
    if (!syscon_field_writable((const uint8_t *)key) ||
        !syscon_field_writable((const uint8_t *)value) || strlen(key) >= 31 || strlen(value) >= 31)
        return 0;
    int slot = first_blank(store);
    return slot < 0 ? 0 : write_slot(store, (unsigned)slot, key, value);
}

int syscon_store_compact(syscon_store *store, const char *key, const char *value) {
    /* 0x2abc is specific to the fifteen-slot runtime namespace, not identity. */
    if (store->count != 15) return -2;
    char kept[8][2][31];
    strncpy(kept[0][0], key, 30); kept[0][0][30] = 0;
    strncpy(kept[0][1], value, 30); kept[0][1][30] = 0;
    unsigned count = 1;
    for (int i = 14; i >= 0; --i) {
        const syscon_slot *slot = &store->slots[i];
        if (slot->key[0] == 0xff || !syscon_field_readable(slot->key) ||
            syscon_checksum31(slot->key) != slot->key_checksum ||
            syscon_checksum31(slot->value) != slot->value_checksum) continue;
        char candidate[31];
        strncpy(candidate, (const char *)slot->key, 30); candidate[30] = 0;
        unsigned j;
        for (j = 0; j < count; ++j)
            if (strncmp(kept[j][0], candidate, 30) == 0) break;
        if (j != count) continue;
        if (count == 8) return 0;
        memcpy(kept[count][0], candidate, 31);
        strncpy(kept[count][1], (const char *)slot->value, 30);
        kept[count][1][30] = 0;
        ++count;
    }
    if (!syscon_store_erase(store)) return 0;
    for (unsigned i = 0; i < count; ++i) {
        int slot = first_blank(store);
        if (slot < 0) return 0;
        int result = write_slot(store, (unsigned)slot, kept[i][0], kept[i][1]);
        if (result != 1) return result;
    }
    return 1;
}

int syscon_config_set(syscon_store *store, const char *key, const char *value) {
    if (strlen(key) >= 31 || strlen(value) >= 31 ||
        !syscon_field_writable((const uint8_t *)key) || !syscon_field_writable((const uint8_t *)value))
        return 0;
    char previous[32];
    int found = syscon_store_get(store, key, previous);
    if (found < 0) return found;
    if (found && strcmp(previous, value) == 0) return 1;
    int slot = first_blank(store);
    if (slot < 0) return syscon_store_compact(store, key, value);
    if (!value[0]) return 0;
    return write_slot(store, (unsigned)slot, key, value);
}

int syscon_store_init(syscon_store *store) {
    char value[32];
    if (syscon_store_get(store, "confVersion", value)) return 1;
    (void)syscon_store_erase(store); /* Original ignores erase and append status. */
    (void)syscon_store_append(store, "confVersion", "1");
    return syscon_store_get(store, "confVersion", value) ? 1 : store_fault(store);
}

static uint32_t timer_value(syscon_store *store, const char *key) {
    char text[32], *end;
    uint32_t value = 3;
    if (syscon_store_get(store, key, text) == 1) {
        long long parsed = strtoll(text, &end, 10);
        /* Original long is signed 32 bits and saturates on positive overflow. */
        if (end != text && *end == 0 && parsed >= 0)
            value = parsed > INT32_MAX ? INT32_MAX : (uint32_t)parsed;
    }
    return value < 3 ? 3 : value > 30 ? 30 : value;
}

void syscon_config_load(syscon_store *config, syscon_store *identity, uint8_t packed[22]) {
    static const char *keys[6] = {"sys.auto_boot", "sys.wake_pin_enable",
        "sys.color_debug_enable", "sys.fastboot_enabled", "sys.demo_enabled", "sys.enable_5v_when_off"};
    memset(packed, 0, 22);
    char text[32];
    for (unsigned i = 0; i < 6; ++i) {
        if (syscon_store_get(config, keys[i], text) == 1)
            packed[i] = strcmp(text, "true") == 0 || strcmp(text, "1") == 0;
    }
    uint32_t edl = timer_value(config, "sys.edl_timer");
    uint32_t shutdown = timer_value(config, "sys.shutdown_timer");
    for (unsigned i = 0; i < 4; ++i) {
        packed[6+i] = (uint8_t)(edl >> (8*i));
        packed[10+i] = (uint8_t)(shutdown >> (8*i));
    }
    if (syscon_store_get(identity, "hw_revision", text) == 1)
        strncpy((char *)packed+14, text, 8);
    packed[21] = 0;
}
