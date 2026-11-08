#ifndef SYSCON_PROTOCOL_TARGET_H
#define SYSCON_PROTOCOL_TARGET_H
#include <stdint.h>
typedef uint32_t (*syscon_target_command)(uint32_t arguments, uint32_t printer);
typedef struct __attribute__((packed)) {
    const char *name;
    syscon_target_command handler;
    uint8_t policy, uppercase;
    const char *help;
} syscon_target_command_record;
_Static_assert(sizeof(syscon_target_command_record) == 14, "Original packed command record");
extern const syscon_target_command_record syscon_target_commands[];
extern const uint32_t syscon_target_command_count;
void syscon_target_protocol_poll(uint32_t context);
extern void syscon_target_mfg_logger(const char *, ...);
uint32_t syscon_target_cmd_help(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_batcheck(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_error(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_log(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_diag(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_version(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_config_set(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_config_get(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_config_find(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_config_erase(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_config_dump(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_config_id_set(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_config_id_get(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_config_id_find(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_config_id_erase(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_config_id_dump(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_read_pwr(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_set_rgb(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_set_pattern(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_ledstatus(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_key_mode(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_modem_on(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_modem_off(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_modem_direct(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_modem_dbg(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_shutdown_reason(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_mcu_reboot(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_mcu_sleep(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_wake_after(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_config_internal(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_keys(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_pwrstatus(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_ioexp_read(uint32_t arguments, uint32_t printer);
uint32_t syscon_target_cmd_gpio_read(uint32_t arguments, uint32_t printer);
#endif
