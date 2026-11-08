/* Source-defined command descriptors; code pointers relocate to source bodies. */
#include "protocol_target.h"
const syscon_target_command_record syscon_target_commands[] =
    {
        {"HELP", syscon_target_cmd_help, 0, 0,
         "Displays a list of available commands ( HELP:; )"}, /* HELP */
        {"BATCHECK", syscon_target_cmd_batcheck, 0, 0,
         "Checks if battery is present ( BATCHECK:; )"}, /* BATCHECK */
        {"ERROR", syscon_target_cmd_error, 1, 0,
         "Test error handling ( ERROR:<[0,1,2]>:; )"}, /* ERROR */
        {"LOG", syscon_target_cmd_log, 1, 0,
         "Enables/disables logging ( LOG:<[0,1]>:; )"}, /* LOG */
        {"DIAG", syscon_target_cmd_diag, 1, 0,
         "Enables/disables diagnostic ( DIAG:<[0,1]>:; )"}, /* DIAG */
        {"VERSION", syscon_target_cmd_version, 0, 0,
         "Displays MCU firmware version ( VERSION:; )"}, /* VERSION */
        {"CONFIG_SET", syscon_target_cmd_config_set, 1, 0,
         "Sets configuration values ( CONFIG_SET:<key>:<value>:; )"}, /* CONFIG_SET */
        {"CONFIG_GET", syscon_target_cmd_config_get, 1, 0,
         "Gets configuration values ( CONFIG_GET:<key>:; )"}, /* CONFIG_GET */
        {"CONFIG_FIND", syscon_target_cmd_config_find, 1, 0,
         "Finds configuration values ( CONFIG_FIND:<key>:; )"}, /* CONFIG_FIND */
        {"CONFIG_ERASE", syscon_target_cmd_config_erase, 1, 0,
         "Erases all configuration values ( CONFIG_ERASE:<password>:; )"}, /* CONFIG_ERASE */
        {"CONFIG_DUMP", syscon_target_cmd_config_dump, 0, 0,
         "Dumps all configuration values ( CONFIG_DUMP:; )"}, /* CONFIG_DUMP */
        {"CONFIG_ID_SET", syscon_target_cmd_config_id_set, 1, 0,
         "Sets configuration values ( CONFIG_ID_SET:<key>:<value>:; )"}, /* CONFIG_ID_SET */
        {"CONFIG_ID_GET", syscon_target_cmd_config_id_get, 1, 0,
         "Gets configuration values ( CONFIG_ID_GET:<key>:; )"}, /* CONFIG_ID_GET */
        {"CONFIG_ID_FIND", syscon_target_cmd_config_id_find, 1, 0,
         "Finds configuration values ( CONFIG_ID_FIND:<key>:; )"}, /* CONFIG_ID_FIND */
        {"CONFIG_ID_ERASE", syscon_target_cmd_config_id_erase, 1, 0,
         "Erases all configuration values ( CONFIG_ID_ERASE:<password>:; )"}, /* CONFIG_ID_ERASE */
        {"CONFIG_ID_DUMP", syscon_target_cmd_config_id_dump, 0, 0,
         "Dump all configuration values ( CONFIG_ID_DUMP:; )"}, /* CONFIG_ID_DUMP */
        {"READ_PWR", syscon_target_cmd_read_pwr, 0, 0,
         "Reads power status ( READ_PWR:; )"}, /* READ_PWR */
        {"SET_RGB", syscon_target_cmd_set_rgb, 1, 0,
         "Sets RGB values ( SET_RGB:<r>:<g>:<b>:<brightness>:<pattern>:; )"}, /* SET_RGB */
        {"SET_PATTERN", syscon_target_cmd_set_pattern, 1, 0,
         "Sets RGB pattern ( SET_PATTERN:<pattern>:<ms>:; )"}, /* SET_PATTERN */
        {"LEDSTATUS", syscon_target_cmd_ledstatus, 0, 0,
         "Gets the current LED theme, color, brightness, and pattern ( LEDSTATUS:; )"}, /* LEDSTATUS
                                                                                         */
        {"KEY_MODE", syscon_target_cmd_key_mode, 1, 1,
         "Sets PWR key mode ( KEY_MODE:<[DETECT,PASSTHRU]>:; )"}, /* KEY_MODE */
        {"560D_ON", syscon_target_cmd_modem_on, 1, 1,
         "Powers on SG560D ( 560D_ON:<[NORMAL,FASTBOOT,FCT,EDL]>:; )"}, /* 560D_ON */
        {"POWER", syscon_target_cmd_modem_on, 1, 1,
         "Powers on SG560D ( 560D_ON/POWER:<[NORMAL,FASTBOOT,FCT,EDL]>:; )"}, /* POWER */
        {"560D_OFF", syscon_target_cmd_modem_off, 1, 1,
         "Powers off SG560D ( 560D_OFF:<[SOFT,HARD]>:; )"}, /* 560D_OFF */
        {"560D_DIRECT", syscon_target_cmd_modem_direct, 1, 1,
         "Forward payload to SG560D ( 560D_DIRECT:<payload>:; )"}, /* 560D_DIRECT */
        {"560D_DBG", syscon_target_cmd_modem_dbg, 1, 1,
         "Enables/Disables debug for SG560D ( 560D_DBG:<[ON,OFF]>:; )"}, /* 560D_DBG */
        {"SHUTDOWN_REASON", syscon_target_cmd_shutdown_reason, 1, 1,
         "Sets shutdown reason ( "
         "SHUTDOWN_REASON:<[REBOOT,POWEROFF,BATTERY_LOW,THERMAL_HIGH,THERMAL_LOW]>:; )"}, /* SHUTDOWN_REASON
                                                                                           */
        {"MCU_REBOOT", syscon_target_cmd_mcu_reboot, 2, 1,
         "Reboots the MCU ( MCU_REBOOT/REBOOT:<optional HARD|SOFT>:; )"}, /* MCU_REBOOT */
        {"REBOOT", syscon_target_cmd_mcu_reboot, 2, 1,
         "Reboots the MCU ( MCU_REBOOT/REBOOT:<optional HARD|SOFT>:; )"}, /* REBOOT */
        {"MCU_SLEEP", syscon_target_cmd_mcu_sleep, 0, 1,
         "Makes the MCU enter sleep mode ( MCU_SLEEP:; )"}, /* MCU_SLEEP */
        {"WAKE_AFTER", syscon_target_cmd_wake_after, 2, 1,
         "Powers on after N seconds, 0 cancels, no arg reports ( WAKE_AFTER:<optional seconds>:; "
         ")"}, /* WAKE_AFTER */
        {"CONFIG_INTERNAL", syscon_target_cmd_config_internal, 0, 1,
         "Gets the non-volatile data ( CONFIG_INTERNAL:; )"}, /* CONFIG_INTERNAL */
        {"KEYS", syscon_target_cmd_keys, 1, 1,
         "Control MCU keys ( KEYS:<[up,down,power]>:; )"}, /* KEYS */
        {"PWRSTATUS", syscon_target_cmd_pwrstatus, 0, 1,
         "Gets the current power status ( PWRSTATUS:; )"}, /* PWRSTATUS */
        {"STATUS", syscon_target_cmd_pwrstatus, 0, 1,
         "Gets the current power status ( STATUS:; )"}, /* STATUS */
        {"IOEXP_READ", syscon_target_cmd_ioexp_read, 1, 1,
         "Gets an IO expander pin value ( IOEXP_READ:<pin>:; )"}, /* IOEXP_READ */
        {"GPIO_READ", syscon_target_cmd_gpio_read, 1, 1,
         "Gets a MCU GPIO pin value ( GPIO_READ:<pin>:; )"}, /* GPIO_READ */
};

const uint32_t syscon_target_command_count =
    sizeof(syscon_target_commands) / sizeof(syscon_target_commands[0]);
