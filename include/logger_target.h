#ifndef SYSCON_LOGGER_TARGET_H
#define SYSCON_LOGGER_TARGET_H
#include <stdint.h>
/* Target-only original ARM32 ABI, including exposed private buffer layout. */
void syscon_logger_target_vlog(uint32_t,const char *,const char *,uint32_t);
void syscon_logger_target(uint32_t,const char *,const char *,...);
void syscon_logger_target_mfg(const char *,...);
uint32_t syscon_logger_target_vformat(uint8_t *,uint32_t,const char *,uint32_t);
uint32_t syscon_logger_target_snprintf(uint8_t *,uint32_t,const char *,...);
void syscon_logger_target_sg560d(const char *,...);
void syscon_logger_target_body(uint8_t *,uint32_t,const char *,const char *,uint32_t);
void syscon_logger_target_sg_body(uint8_t *,const char *,uint32_t);
/* Link-compatible names for existing reconstructed callers. */
void syscon_target_logger(uint32_t,const char *,const char *,...);
void syscon_target_mfg_logger(const char *,...);
void syscon_target_sg560d_printf(const char *,...);
uint32_t syscon_target_snprintf(uint8_t *,uint32_t,const char *,...);
#endif
