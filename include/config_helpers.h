#ifndef SYSCON_TARGET_CONFIG_HELPERS_H
#define SYSCON_TARGET_CONFIG_HELPERS_H
#include <stdint.h>
/* Original ARM32 entry ABI; pointers refer to the target address space. */
uint32_t syscon_cfg_indexed_get(uint32_t,uint32_t,char *,char *);
uint32_t syscon_cfg_runtime_slot_blank(uint32_t);
uint32_t syscon_cfg_identity_slot_blank(uint32_t);
uint32_t syscon_cfg_runtime_slot_count(void);
uint32_t syscon_cfg_identity_slot_count(void);
uint32_t syscon_cfg_identity_erase(const char *);
uint32_t syscon_cfg_identity_append(const char *,const char *);
uint32_t syscon_cfg_identity_get(char *,char *);
uint32_t syscon_cfg_identity_indexed_get(char *,char *);
uint32_t syscon_cfg_runtime_get(char *,char *);
uint32_t syscon_cfg_runtime_erase(const char *);
uint32_t syscon_cfg_runtime_indexed_get(char *,char *);
/* Shared configuration bodies, also reconstructed at their original ABI. */
uint32_t syscon_cfg_field_readable(const uint8_t *);
uint32_t syscon_cfg_field_writable(const uint8_t *);
uint32_t syscon_cfg_checksum(const uint8_t *);
uint32_t syscon_cfg_slot_valid(const uint8_t *);
uint32_t syscon_cfg_read_slot(const uint8_t *,char *);
uint32_t syscon_cfg_find_slot(uint32_t,uint32_t,char *,uint32_t,uint32_t *);
uint32_t syscon_cfg_store_get(uint32_t,uint32_t,char *,char *);
/* Source-backed storage/load dependencies; assertion remains an external
 * firmware boundary. Logger is provided by the target formatting adapter. */
uint32_t syscon_cfg_store_erase(uint32_t,uint32_t);
uint32_t syscon_cfg_store_append(uint32_t,uint32_t,const char *,const char *);
void syscon_cfg_load(void);
void syscon_cfg_assert(const char *,uint32_t,const char *);
void syscon_target_logger(uint32_t,const char *,const char *,...);
uint32_t syscon_cfg_write_slot(uint32_t,const char *,const char *);
void syscon_cfg_flash_report(void);
void syscon_cfg_bool_get(uint32_t,char *,uint8_t *);
void syscon_cfg_u32_get(uint32_t,char *,uint32_t *);
uint32_t syscon_cfg_compact(uint32_t base, const char *key, const char *value);
void syscon_cfg_store_init(uint32_t,uint32_t);
void syscon_target_config_init(void);
uint32_t syscon_cfg_runtime_update(const char *key, const char *value);
#endif
