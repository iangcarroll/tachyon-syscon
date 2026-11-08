/* Original-ABI namespace entry points, recovered from syscon1.0.52. */
#include "config_helpers.h"
#include "config_text.h"
#include "runtime_memory.h"
#define CONF SYSCON_CFG_LOG_TAG
_Static_assert(sizeof(void *) == 4, "ARM32 target only");
uint32_t syscon_cfg_indexed_get(uint32_t base, uint32_t bytes, char *key, char *value)
{
    if (syscon_rt_strlen(key) >= 31) {
        syscon_target_logger(1, CONF, SYSCON_CFG_KEY_TOO_LONG);
        return 0;
    }
    uint32_t slot = 0;
    uint32_t found = syscon_cfg_find_slot(base, bytes, key, 2, &slot);
    return found ? syscon_cfg_read_slot((const uint8_t *)(uintptr_t)slot, value) : 0;
}
static uint32_t slot_blank(uint32_t base, uint32_t limit, uint32_t index)
{
    if (index >= limit)
        return 1;
    const volatile uint8_t *slot = (const volatile uint8_t *)(uintptr_t)(base + 64 * index);
    for (unsigned i = 0; i < 64; i++)
        if (slot[i] != 255)
            return 0;
    return 1;
}
uint32_t syscon_cfg_runtime_slot_blank(uint32_t index)
{
    return slot_blank(0xfc00, 15, index);
}
uint32_t syscon_cfg_identity_slot_blank(uint32_t index)
{
    return slot_blank(0xf800, 16, index);
}
uint32_t syscon_cfg_runtime_slot_count(void)
{
    return 15;
}
uint32_t syscon_cfg_identity_slot_count(void)
{
    return 16;
}
static void failed_version(const char *message, uint32_t line)
{
    syscon_target_logger(1, CONF, message);
    const char *path = SYSCON_CFG_ORIGINAL_SOURCE_PATH, *file = path;
    if (syscon_rt_strrchr(path, '/'))
        file = (const char *)syscon_rt_strrchr(path, '/') + 1;
    syscon_cfg_assert(file, line, SYSCON_CFG_ZERO);
}
uint32_t syscon_cfg_identity_erase(const char *password)
{
    if (syscon_rt_strcmp(password, SYSCON_CFG_IDENTITY_ERASE_PASSWORD)) {
        syscon_target_logger(1, CONF, SYSCON_CFG_INVALID_PASSWORD);
        return 0;
    }
    if (!syscon_cfg_store_erase(0xf800, 1024))
        return 0;
    uint32_t result = syscon_cfg_store_append(0xf800, 1024, SYSCON_CFG_KEY_VERSION, SYSCON_CFG_ONE);
    char version[32];
    if (!syscon_cfg_store_get(0xf800, 1024, (char *)SYSCON_CFG_KEY_VERSION, version))
        failed_version(SYSCON_CFG_VERSION_FAILED, 0x3a4);
    return result;
}
uint32_t syscon_cfg_identity_append(const char *key, const char *value)
{
    uint32_t result = syscon_cfg_store_append(0xf800, 1024, key, value);
    if (result)
        syscon_cfg_load();
    return result;
}
uint32_t syscon_cfg_identity_get(char *key, char *out)
{
    return syscon_cfg_store_get(0xf800, 1024, key, out);
}
uint32_t syscon_cfg_identity_indexed_get(char *key, char *out)
{
    return syscon_cfg_indexed_get(0xf800, 1024, key, out);
}
uint32_t syscon_cfg_runtime_get(char *key, char *out)
{
    return syscon_cfg_store_get(0xfc00, 960, key, out);
}
uint32_t syscon_cfg_runtime_erase(const char *password)
{
    if (syscon_rt_strcmp(password, SYSCON_CFG_RUNTIME_ERASE_PASSWORD)) {
        syscon_target_logger(1, CONF, SYSCON_CFG_INVALID_PASSWORD);
        return 0;
    }
    if (!syscon_cfg_store_erase(0xfc00, 960))
        return 0;
    uint32_t result = syscon_cfg_store_append(0xfc00, 960, SYSCON_CFG_KEY_VERSION, SYSCON_CFG_ONE);
    char version[32];
    if (!syscon_cfg_store_get(0xfc00, 960, (char *)SYSCON_CFG_KEY_VERSION, version))
        failed_version(SYSCON_CFG_RUNTIME_VERSION_FAILED, 0x41a);
    syscon_cfg_load();
    return result;
}
uint32_t syscon_cfg_runtime_indexed_get(char *key, char *out)
{
    return syscon_cfg_indexed_get(0xfc00, 960, key, out);
}
