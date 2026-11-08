#include "firmware_version.h"
/* Original target command ABI. Printer is a real variadic ARM callback.
 * Inputs are not sanitized beyond the original checks (notably SET_RGB). */
#include "protocol_target.h"
#include "protocol_state.h"
#include "runtime_memory.h"
#include "runtime_support.h"
#include "runtime_scan.h"
#include "rgb_target.h"
#include "power_manager_target.h"
#include "power_policy_target.h"
#include "power_key_target.h"
#include "ioexpander_target.h"
#include "scheduling_target.h"
#include "diagnostics_target.h"
#include "mspm0_core_target.h"
#include "logger_target.h"
#include "sg560d_target.h"
#include "application_target.h"
#define TEXT(a) ((const char *)(uintptr_t)(a))
#define POINTER(p) ((uint32_t)(uintptr_t)(p))
#define PRINT(p) ((uint32_t (*)(const char *, ...))(uintptr_t)(p))
extern void syscon_mcu_sleep(void);
static uint32_t bad(uint32_t printer)
{
    PRINT(printer)("Invalid parameters. Use \"HELP:;\" for more details.");
    return 0;
}
static int equal(uint32_t args, const char *text)
{
    return syscon_rt_strcmp(TEXT(args), text) == 0;
}
uint32_t syscon_target_cmd_version(uint32_t args, uint32_t printer)
{
    (void)args;
    PRINT(printer)("Version=%s", syscon_firmware_version);
    return 1;
}
uint32_t syscon_target_cmd_help(uint32_t args, uint32_t printer)
{
    (void)args;
    PRINT(printer)("Available commands:");
    for (unsigned i = 0; i < syscon_target_command_count; ++i)
        PRINT(printer)("%s - %s", syscon_target_commands[i].name, syscon_target_commands[i].help);
    return 1;
}
uint32_t syscon_target_cmd_ioexp_read(uint32_t args, uint32_t printer)
{
    uint32_t pin = 0;
    uint8_t value;
    if (syscon_rt_sscanf(TEXT(args), "%d", &pin) != 1)
        return bad(printer);
    if (syscon_target_ioexpander_read((uint8_t)pin, &value)) {
        PRINT(printer)("IOEXP_READ Error");
        return 0;
    }
    PRINT(printer)("Pin %d value: %d", pin, (uint32_t)value);
    return 1;
}
uint32_t syscon_target_cmd_gpio_read(uint32_t args, uint32_t printer)
{
    uint32_t pin = 0;
    if (syscon_rt_sscanf(TEXT(args), "%d", &pin) != 1)
        return bad(printer);
    uint32_t value = syscon_target_gpio_read((uint16_t)pin);
    PRINT(printer)("Pin %d value: %d", pin, value);
    return 1;
}
uint32_t syscon_target_cmd_pwrstatus(uint32_t args, uint32_t printer)
{
    (void)args;
    syscon_target_power_report(printer);
    return 1;
}
uint32_t syscon_target_cmd_wake_after(uint32_t args, uint32_t printer)
{
    if (!args) {
        int32_t seconds = (int32_t)syscon_target_modem_wake_remaining();
        if (seconds < 0)
            PRINT(printer)("Timed wake: none");
        else
            PRINT(printer)("Timed wake: in %ds", seconds);
        return 1;
    }
    uint32_t seconds = 0;
    if (syscon_rt_sscanf(TEXT(args), "%d", &seconds) != 1 || seconds > 259200)
        return bad(printer);
    syscon_target_modem_wake_schedule(seconds);
    return 1;
}
uint32_t syscon_target_cmd_mcu_sleep(uint32_t args, uint32_t printer)
{
    (void)args;
    PRINT(printer)(" MCU sleep");
    syscon_mcu_sleep();
    return 1;
}
uint32_t syscon_target_cmd_mcu_reboot(uint32_t args, uint32_t printer)
{
    if (args && !equal(args, "HARD:;") && !equal(args, "SOFT:;"))
        return bad(printer);
    int hard = args && equal(args, "HARD:;");
    syscon_target_logger(3, "MFGD", "Reset MCU - %s", (hard ? "hard" : "soft"));
    if (hard) {
        (void)syscon_target_ioexpander_reset();
        syscon_target_retained_clear_registers();
    }
    syscon_target_timer_delay(500);
    __asm__ volatile("dsb sy" ::: "memory");
    *(volatile uint32_t *)(uintptr_t)0xe000ed0c = 0x05fa0004;
    __asm__ volatile("dsb sy" ::: "memory");
    for (;;)
        __asm__ volatile("nop");
}
uint32_t syscon_target_cmd_shutdown_reason(uint32_t args, uint32_t printer)
{
    uint32_t reason;
    if (equal(args, "REBOOT:;"))
        reason = 1;
    else if (equal(args, "POWEROFF:;") || equal(args, "USER:;"))
        reason = 2;
    else if (equal(args, "BATTERY_LOW:;"))
        reason = 3;
    else if (equal(args, "THERMAL_HIGH:;"))
        reason = 4;
    else if (equal(args, "THERMAL_LOW:;"))
        reason = 5;
    else
        return bad(printer);
    syscon_target_shutdown_set(reason);
    return 1;
}
uint32_t syscon_target_cmd_modem_direct(uint32_t args, uint32_t printer)
{
    (void)printer;
    uint32_t length = syscon_rt_strlen(TEXT(args)) - 2;
    (void)syscon_target_modem_raw_send(args, length);
    uint8_t newline[3];
    syscon_rt_memcpy(newline, "\r\n", 3);
    (void)syscon_target_modem_raw_send(POINTER(newline), 2);
    return 1;
}
uint32_t syscon_target_cmd_modem_on(uint32_t args, uint32_t printer)
{
    uint32_t result;
    if (equal(args, "NORMAL:;"))
        result = syscon_target_modem_poweron();
    else if (equal(args, "FASTBOOT:;"))
        result = syscon_target_modem_fastboot();
    else if (equal(args, "FCT:;"))
        result = syscon_target_modem_fct();
    else if (equal(args, "EDL:;"))
        result = syscon_target_modem_edl();
    else
        return bad(printer);
    return result == 0;
}
uint32_t syscon_target_cmd_ledstatus(uint32_t args, uint32_t printer)
{
    (void)args;
    uint8_t config[6];
    syscon_rt_memset(config, 0, 6);
    uint32_t result = syscon_target_rgb_get_config(POINTER(config));
    if (result) {
        uint32_t theme = syscon_target_rgb_state_name(config[0]),
                 pattern = syscon_target_rgb_pattern_name(config[5]);
        PRINT(printer)("LEDSTATUS theme=%s red=%u green=%u blue=%u brightness=%u pattern=%s",
                       TEXT(theme), (uint32_t)config[1], (uint32_t)config[2], (uint32_t)config[3],
                       (uint32_t)config[4], TEXT(pattern));
    }
    return result;
}
uint32_t syscon_target_cmd_set_pattern(uint32_t args, uint32_t printer)
{
    uint32_t state = (uint32_t)syscon_rt_atoi(TEXT(args));
    const char *colon = syscon_rt_strchr(TEXT(args), ':');
    int32_t duration = colon ? syscon_rt_atoi(colon + 1) : 0;
    if (state >= 10 || duration < 0)
        return bad(printer);
    return syscon_target_rgb_preset((uint8_t)state, (uint32_t)duration) == 0;
}
uint32_t syscon_target_cmd_set_rgb(uint32_t args, uint32_t printer)
{
    uint8_t config[5];
    syscon_rt_memset(config, 0, 5);
    const char *const labels[5] = {"R: ", "G: ", "B: ", "Brightness: ", "Pattern: "};
    for (unsigned i = 0; i < 5; ++i) {
        const char *colon = syscon_rt_strchr(TEXT(args), ':');
        int32_t distance = (int32_t)(POINTER(colon) - args);
        if (!colon || distance > 3)
            return bad(printer);
        char token[4];
        uint32_t length = (uint8_t)distance;
        syscon_rt_strncpy(token, TEXT(args), length);
        token[length] = 0;
        PRINT(printer)(labels[i]);
        PRINT(printer)(token); /* Original passes the user token as a format. */
        config[i] = (uint8_t)syscon_rt_atoi(token);
        args = POINTER(colon) + 1;
    }
    if (config[4] >= 5)
        return bad(printer);
    return syscon_target_rgb_configure(POINTER(config)) == 0;
}
uint32_t syscon_target_cmd_read_pwr(uint32_t args, uint32_t printer)
{
    (void)args;
    const char *const labels[5] = {"VPH: ", "5V: ", "VBAT: ", "1V8: ", "VUSB: "};
    for (unsigned i = 0; i < 5; ++i) {
        uint32_t value = syscon_target_power_measure(12 + i);
        PRINT(printer)("%s: %dmV", labels[i], value);
    }
    return 1;
}
/* BATCHECK invokes an active power-route probe, with no processor-off guard. */
uint32_t syscon_target_cmd_batcheck(uint32_t args, uint32_t printer)
{
    (void)args;
    (void)printer;
    syscon_target_power_battery_probe();
    return 1;
}
uint32_t syscon_target_cmd_modem_dbg(uint32_t args, uint32_t printer)
{
    const char *message;
    if (equal(args, "ON:;")) {
        syscon_protocol_debug = 1;
        message = "Debug enabled";
    } else if (equal(args, "OFF:;")) {
        syscon_protocol_debug = 0;
        message = "Debug disabled";
    } else
        return bad(printer);
    PRINT(printer)(message);
    return 1;
}
uint32_t syscon_target_cmd_keys(uint32_t args, uint32_t printer)
{
    uint32_t pin;
    if (equal(args, "UP:;"))
        pin = 0x27;
    else if (equal(args, "DOWN:;"))
        pin = 0x1d;
    else if (equal(args, "POWER:;"))
        pin = 8;
    else
        return bad(printer);
    (void)syscon_target_modem_key_pulse(pin, 0);
    return 1;
}
uint32_t syscon_target_cmd_modem_off(uint32_t args, uint32_t printer)
{
    uint32_t hard;
    if (equal(args, "SOFT:;"))
        hard = 0;
    else if (equal(args, "HARD:;"))
        hard = 1;
    else
        return bad(printer);
    return syscon_target_modem_poweroff(hard);
}
uint32_t syscon_target_cmd_diag(uint32_t args, uint32_t printer)
{
    uint8_t first = *(const volatile uint8_t *)(uintptr_t)args;
    if (first != '0' && first != '1')
        return bad(printer);
    syscon_target_diagnostics_enable(first - '0');
    return 1;
}
uint32_t syscon_target_cmd_log(uint32_t args, uint32_t printer)
{
    uint8_t first = *(const volatile uint8_t *)(uintptr_t)args;
    if (first != '0' && first != '1')
        return bad(printer);
    syscon_target_log_enable(first - '0');
    return 1;
}
uint32_t syscon_target_cmd_error(uint32_t args, uint32_t printer)
{
    (void)printer;
    int32_t value = syscon_rt_atoi(TEXT(args));
    if (value == 0) {
        const char *file =
            "/home/runner/work/tachyon-syscon/tachyon-syscon/app/src/mfg_command.cpp";
        if (syscon_rt_strrchr(file, '/'))
            file = (const char *)syscon_rt_strrchr(file, '/') + 1;
        syscon_target_assert(POINTER(file), 0x110, POINTER("0"));
        return 1;
    }
    if (value == 1)
        return 1;
    if (value == 2) {
        syscon_target_logger(1, "MFGD", "-1 failed: %d", UINT32_MAX);
        return 1;
    }
    syscon_target_logger(1, "MFGD", "Invalid error test command");
    return 0;
}
uint32_t syscon_target_cmd_key_mode(uint32_t args, uint32_t printer)
{
    uint32_t mode;
    if (equal(args, "DETECT:;"))
        mode = 1;
    else if (equal(args, "PASSTHRU:;"))
        mode = 0;
    else
        return bad(printer);
    syscon_target_powerkey_mode(mode);
    return 1;
}
