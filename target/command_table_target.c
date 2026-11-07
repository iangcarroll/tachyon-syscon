/* Source-defined command descriptors; code pointers relocate to source bodies. */
#include "protocol_target.h"
const syscon_target_command_record syscon_target_commands[37]={
    {0xbb09,syscon_target_cmd_help,0,0,0xbb0e}, /* HELP */
    {0xbb3f,syscon_target_cmd_batcheck,0,0,0xbb48}, /* BATCHECK */
    {0xbb74,syscon_target_cmd_error,1,0,0xbb7a}, /* ERROR */
    {0xbba4,syscon_target_cmd_log,1,0,0xbba8}, /* LOG */
    {0xb290,syscon_target_cmd_diag,1,0,0xbbd3}, /* DIAG */
    {0xbc02,syscon_target_cmd_version,0,0,0xbc0a}, /* VERSION */
    {0xbc36,syscon_target_cmd_config_set,1,0,0xbc41}, /* CONFIG_SET */
    {0xbc7a,syscon_target_cmd_config_get,1,0,0xbc85}, /* CONFIG_GET */
    {0xbcb6,syscon_target_cmd_config_find,1,0,0xbcc2}, /* CONFIG_FIND */
    {0xbcf5,syscon_target_cmd_config_erase,1,0,0xbd02}, /* CONFIG_ERASE */
    {0xbd40,syscon_target_cmd_config_dump,0,0,0xbd4c}, /* CONFIG_DUMP */
    {0xbd7d,syscon_target_cmd_config_id_set,1,0,0xbd8b}, /* CONFIG_ID_SET */
    {0xbdc7,syscon_target_cmd_config_id_get,1,0,0xbdd5}, /* CONFIG_ID_GET */
    {0xbe09,syscon_target_cmd_config_id_find,1,0,0xbe18}, /* CONFIG_ID_FIND */
    {0xbe4e,syscon_target_cmd_config_id_erase,1,0,0xbe5e}, /* CONFIG_ID_ERASE */
    {0xbe9f,syscon_target_cmd_config_id_dump,0,0,0xbeae}, /* CONFIG_ID_DUMP */
    {0xbee1,syscon_target_cmd_read_pwr,0,0,0xbeea}, /* READ_PWR */
    {0xbf0c,syscon_target_cmd_set_rgb,1,0,0xbf14}, /* SET_RGB */
    {0xbf55,syscon_target_cmd_set_pattern,1,0,0xbf61}, /* SET_PATTERN */
    {0xbf93,syscon_target_cmd_ledstatus,0,0,0xbf9d}, /* LEDSTATUS */
    {0xbfe8,syscon_target_cmd_key_mode,1,1,0xbff1}, /* KEY_MODE */
    {0xc026,syscon_target_cmd_modem_on,1,1,0xc02e}, /* 560D_ON */
    {0xc069,syscon_target_cmd_modem_on,1,1,0xc06f}, /* POWER */
    {0xc0b0,syscon_target_cmd_modem_off,1,1,0xc0b9}, /* 560D_OFF */
    {0xc0e8,syscon_target_cmd_modem_direct,1,1,0xc0f4}, /* 560D_DIRECT */
    {0xc12a,syscon_target_cmd_modem_dbg,1,1,0xc133}, /* 560D_DBG */
    {0xc16f,syscon_target_cmd_shutdown_reason,1,1,0xc17f}, /* SHUTDOWN_REASON */
    {0xc1e3,syscon_target_cmd_mcu_reboot,2,1,0xc1ee}, /* MCU_REBOOT */
    {0xc1e7,syscon_target_cmd_mcu_reboot,2,1,0xc1ee}, /* REBOOT */
    {0xc22b,syscon_target_cmd_mcu_sleep,0,1,0xc235}, /* MCU_SLEEP */
    {0xc264,syscon_target_cmd_wake_after,2,1,0xc26f}, /* WAKE_AFTER */
    {0xc2c8,syscon_target_cmd_config_internal,0,1,0xc2d8}, /* CONFIG_INTERNAL */
    {0xc309,syscon_target_cmd_keys,1,1,0xc30e}, /* KEYS */
    {0xc33c,syscon_target_cmd_pwrstatus,0,1,0xc346}, /* PWRSTATUS */
    {0xbf96,syscon_target_cmd_pwrstatus,0,1,0xc374}, /* STATUS */
    {0xc39f,syscon_target_cmd_ioexp_read,1,1,0xc3aa}, /* IOEXP_READ */
    {0xc3df,syscon_target_cmd_gpio_read,1,1,0xc3e9}, /* GPIO_READ */
};
