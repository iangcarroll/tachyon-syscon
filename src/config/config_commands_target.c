/* Original-ABI configuration command handlers with real scan/store helpers. */
#include "config_commands_target.h"
#include "config_helpers.h"
#include "config_text.h"
#include "diagnostics_target.h"
#include "runtime_scan.h"
#include "runtime_memory.h"
#include "mspm0_core_target.h"
#include <stdint.h>
#define ARGUMENT_TEXT(a) ((const char *)(uintptr_t)(uint32_t)(a))
typedef void (*printer_t)(const char *, ...);
typedef uint32_t (*get_t)(char *, char *);
typedef uint32_t (*set_t)(const char *, const char *);
static uint32_t get(uint32_t arguments, uint32_t printer, get_t lookup, const char *found)
{
    char key[32], value[32];
    printer_t print = (printer_t)(uintptr_t)printer;
    if (syscon_rt_sscanf(ARGUMENT_TEXT(arguments), SYSCON_CFG_SCAN_KEY, key) != 1) {
        print(SYSCON_CFG_INVALID_PARAMETERS);
        return 0;
    }
    uint32_t result = lookup(key, value);
    if (result)
        print(found, key, value);
    else
        print(SYSCON_CFG_NOT_FOUND, key);
    return result;
}
/* A separate helper adds an observable eight-byte frame: compaction logs the
 * original stack usage. Keep the handler's original single 80-byte frame. */
__attribute__((always_inline)) static inline uint32_t set(uint32_t arguments, uint32_t printer,
                                                          set_t append)
{
    char key[32], value[32];
    printer_t print = (printer_t)(uintptr_t)printer;
    if (syscon_rt_sscanf(ARGUMENT_TEXT(arguments), SYSCON_CFG_SCAN_PAIR, key, value) != 2) {
        print(SYSCON_CFG_INVALID_PARAMETERS);
        return 0;
    }
    uint32_t result = append(key, value);
    if (result)
        print(SYSCON_CFG_ENTRY, key, value);
    else
        print(SYSCON_CFG_REFUSED, key);
    return result;
}
static uint32_t erase(uint32_t arguments, uint32_t printer, uint32_t (*erase_store)(const char *),
                      const char *success)
{
    char password[32];
    printer_t print = (printer_t)(uintptr_t)printer;
    if (syscon_rt_sscanf(ARGUMENT_TEXT(arguments), SYSCON_CFG_SCAN_KEY, password) != 1) {
        print(SYSCON_CFG_INVALID_PARAMETERS);
        return 0;
    }
    uint32_t result = erase_store(password);
    print((result ? success : SYSCON_CFG_INVALID_PASSWORD));
    return result;
}
uint32_t syscon_target_cmd_config_id_find(uint32_t a, uint32_t p)
{
    return get(a, p, syscon_cfg_identity_indexed_get, SYSCON_CFG_FOUND_ENTRY);
}
uint32_t syscon_target_cmd_config_find(uint32_t a, uint32_t p)
{
    return get(a, p, syscon_cfg_runtime_indexed_get, SYSCON_CFG_FOUND_ENTRY);
}
uint32_t syscon_target_cmd_config_id_get(uint32_t a, uint32_t p)
{
    return get(a, p, syscon_cfg_identity_get, SYSCON_CFG_ENTRY);
}
uint32_t syscon_target_cmd_config_get(uint32_t a, uint32_t p)
{
    return get(a, p, syscon_cfg_runtime_get, SYSCON_CFG_ENTRY);
}
uint32_t syscon_target_cmd_config_id_set(uint32_t a, uint32_t p)
{
    return set(a, p, syscon_cfg_identity_append);
}
uint32_t syscon_target_cmd_config_set(uint32_t a, uint32_t p)
{
    return set(a, p, syscon_cfg_runtime_update);
}
uint32_t syscon_target_cmd_config_id_erase(uint32_t a, uint32_t p)
{
    return erase(a, p, syscon_cfg_identity_erase, SYSCON_CFG_IDENTITY_ERASED);
}
uint32_t syscon_target_cmd_config_erase(uint32_t a, uint32_t p)
{
    return erase(a, p, syscon_cfg_runtime_erase, SYSCON_CFG_RUNTIME_ERASED);
}
void syscon_target_config_dump(uint32_t identity, uint32_t printer)
{
    printer_t print = (printer_t)(uintptr_t)printer;
    char key[32] = {0}, value[32];
    uint32_t count = identity ? syscon_cfg_identity_slot_count() : syscon_cfg_runtime_slot_count();
    uint32_t rejected = 0;
    for (uint32_t index = 0; index != count; ++index) {
        syscon_rt_snprintf(key, 32, SYSCON_CFG_INDEX_FORMAT, index);
        uint32_t found = identity ? syscon_cfg_identity_indexed_get(key, value)
                                  : syscon_cfg_runtime_indexed_get(key, value);
        if (found)
            print(SYSCON_CFG_ENTRY, key, value);
        else {
            uint32_t blank = identity ? syscon_cfg_identity_slot_blank(index)
                                      : syscon_cfg_runtime_slot_blank(index);
            if ((uint8_t)blank != 1) {
                print(SYSCON_CFG_REJECTED_SLOT, index);
                ++rejected;
            }
        }
        syscon_target_watchdog_feed();
        syscon_rt_memset(value, 0, 32);
    }
    print(SYSCON_CFG_END_OF_KEYS);
    if (rejected)
        print(SYSCON_CFG_REJECTED_WARNING, rejected);
}
uint32_t syscon_target_cmd_config_id_dump(uint32_t arguments, uint32_t printer)
{
    (void)arguments;
    syscon_target_config_dump(1, printer);
    return 1;
}
uint32_t syscon_target_cmd_config_dump(uint32_t arguments, uint32_t printer)
{
    (void)arguments;
    syscon_target_config_dump(0, printer);
    return 1;
}
uint32_t syscon_target_cmd_config_internal(uint32_t arguments, uint32_t printer)
{
    (void)arguments;
    printer_t print = (printer_t)(uintptr_t)printer;
    uint32_t flags[6];
    flags[0] = syscon_target_auto_boot();
    flags[1] = syscon_target_wakeup_enabled();
    flags[2] = syscon_target_log_color();
    flags[3] = syscon_target_alt_powerkey();
    flags[4] = syscon_target_demo_enabled();
    flags[5] = syscon_target_keep_5v_when_off();
    uint32_t long_seconds = syscon_target_powerkey_long_seconds(),
             extra_seconds = syscon_target_powerkey_extra_seconds();
    const char *const formats[] = {SYSCON_CFG_DISPLAY_AUTO_BOOT,   SYSCON_CFG_DISPLAY_WAKE_PIN,
                                   SYSCON_CFG_DISPLAY_COLOR_DEBUG, SYSCON_CFG_DISPLAY_FASTBOOT,
                                   SYSCON_CFG_DISPLAY_DEMO,        SYSCON_CFG_DISPLAY_KEEP_5V};
    for (unsigned i = 0; i < 6; ++i)
        print(formats[i], (flags[i] ? SYSCON_CFG_TRUE : SYSCON_CFG_FALSE));
    print(SYSCON_CFG_DISPLAY_EDL_TIMER, long_seconds);
    print(SYSCON_CFG_DISPLAY_SHUTDOWN_TIMER, extra_seconds);
    return 1;
}
