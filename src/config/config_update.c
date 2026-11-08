/* Runtime namespace compaction, update and initialization. */
#include "config_helpers.h"
#include "config_text.h"
#include "runtime_memory.h"
#include <stdint.h>
#define CONF SYSCON_CFG_LOG_TAG
static void feed(void)
{
    *(volatile uint32_t *)(uintptr_t)0x40081108 = 0xa7;
}
uint32_t syscon_cfg_compact(uint32_t base, const char *key, const char *value)
{
    char kept[8][2][31], candidate[31];
    uintptr_t stack_pointer;
    /* Measure this compiled frame; callers and locals may change independently.
     * This is the active ARM stack pointer, not an assumed compiler frame size. */
    __asm__ volatile("mov %0, sp" : "=r"(stack_pointer) : : "memory");
    syscon_target_logger(3, CONF, SYSCON_CFG_COMPACT_STACK, 0x20001000u - stack_pointer);
    feed();
    syscon_rt_strncpy(kept[0][0], key, 30);
    kept[0][0][30] = 0;
    syscon_rt_strncpy(kept[0][1], value, 30);
    kept[0][1][30] = 0;
    syscon_target_logger(3, CONF, SYSCON_CFG_COMPACT_NEW_ENTRY, key, value);
    uint32_t count = 1;
    for (int32_t index = 14; index >= 0; index--) {
        const uint8_t *slot = (const uint8_t *)(uintptr_t)(base + (uint32_t)index * 64);
        if (slot[0] != 255 && syscon_cfg_field_readable(slot) &&
            syscon_cfg_checksum(slot) == slot[31] && syscon_cfg_checksum(slot + 32) == slot[63]) {
            syscon_rt_strncpy(candidate, slot, 30);
            candidate[30] = 0;
            uint32_t existing = 0;
            while (existing < count && syscon_rt_strncmp(kept[existing][0], candidate, 30))
                existing++;
            if (existing == count) {
                if (count > 7) {
                    syscon_target_logger(1, CONF, SYSCON_CFG_COMPACT_CAPACITY, (count + 1) & 255, 8,
                                         15);
                    return 0;
                }
                syscon_rt_strncpy(kept[count][0], candidate, 30);
                kept[count][0][30] = 0;
                syscon_rt_strncpy(kept[count][1], slot + 32, 30);
                kept[count][1][30] = 0;
                count = (count + 1) & 255;
            }
        }
        if (!((uint32_t)index & 3))
            feed();
    }
    syscon_target_logger(3, CONF, SYSCON_CFG_COMPACT_COLLECTED, count);
    feed();
    if (!syscon_cfg_store_erase(base, 960)) {
        syscon_target_logger(1, CONF, SYSCON_CFG_COMPACT_ERASE_FAILED);
        return 0;
    }
    feed();
    uint32_t result = 0;
    for (uint32_t i = 0; i < count; i++) {
        uint32_t slot = 0;
        if (!syscon_cfg_find_slot(base, 960, 0, 0, &slot)) {
            syscon_target_logger(1, CONF, SYSCON_CFG_COMPACT_NO_SLOT, i);
            return 0;
        }
        result = syscon_cfg_write_slot(slot, kept[i][0], kept[i][1]);
        if (!result) {
            syscon_target_logger(1, CONF, SYSCON_CFG_COMPACT_WRITE_FAILED, i, kept[i][0]);
            return 0;
        }
        feed();
    }
    syscon_target_logger(3, CONF, SYSCON_CFG_COMPACT_COMPLETE, count);
    return result;
}
void syscon_cfg_store_init(uint32_t base, uint32_t bytes)
{
    char version[32];
    if (syscon_cfg_store_get(base, bytes, (char *)SYSCON_CFG_KEY_VERSION, version)) {
        syscon_target_logger(3, CONF, SYSCON_CFG_ALREADY_INITIALIZED, base);
        return;
    }
    syscon_target_logger(3, CONF, SYSCON_CFG_INITIALIZING, base);
    (void)syscon_cfg_store_erase(base, bytes);
    (void)syscon_cfg_store_append(base, bytes, SYSCON_CFG_KEY_VERSION, SYSCON_CFG_ONE);
    if (!syscon_cfg_store_get(base, bytes, (char *)SYSCON_CFG_KEY_VERSION, version)) {
        syscon_target_logger(1, CONF, SYSCON_CFG_VERSION_FAILED);
        const char *path = SYSCON_CFG_ORIGINAL_SOURCE_PATH, *file = path;
        if (syscon_rt_strrchr(path, '/'))
            file = (const char *)syscon_rt_strrchr(path, '/') + 1;
        syscon_cfg_assert(file, 0x2db, SYSCON_CFG_ZERO);
    }
}
void syscon_target_config_init(void)
{
    syscon_cfg_store_init(0xf800, 1024);
    syscon_cfg_store_init(0xfc00, 960);
    syscon_cfg_load();
}
uint32_t syscon_cfg_runtime_update(const char *key, const char *value)
{
    if (syscon_rt_strlen(key) >= 31 || syscon_rt_strlen(value) >= 31) {
        syscon_target_logger(1, CONF, SYSCON_CFG_FIELD_TOO_LONG);
        return 0;
    }
    uint32_t valid = syscon_cfg_field_writable((const uint8_t *)key);
    if (valid)
        valid = syscon_cfg_field_writable((const uint8_t *)value);
    if (!valid) {
        syscon_target_logger(1, CONF, SYSCON_CFG_UNREADABLE_FIELD, key);
        return 0;
    }
    char previous[32];
    uint32_t result = syscon_cfg_store_get(0xfc00, 960, (char *)key, previous);
    if (result && !syscon_rt_strcmp(previous, value))
        return result;
    uint32_t slot = 0;
    if (!syscon_cfg_find_slot(0xfc00, 960, (char *)key, 0, &slot)) {
        syscon_target_logger(3, CONF, SYSCON_CFG_COMPACT_REQUIRED);
        result = syscon_cfg_compact(0xfc00, key, value);
    } else {
        if (!syscon_rt_strlen(value))
            return 0;
        result = syscon_cfg_write_slot(slot, key, value);
    }
    if (!result)
        return 0;
    syscon_cfg_load();
    return valid;
}
