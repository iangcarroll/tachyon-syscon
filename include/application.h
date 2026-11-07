#ifndef SYSCON_APPLICATION_H
#define SYSCON_APPLICATION_H
#include "sg560d.h"
void syscon_application_constructors(uint8_t ram[4096],const sg560d_environment *);
void syscon_application_init(uint8_t ram[4096],const sg560d_environment *);
void syscon_application_tick(uint8_t ram[4096],const sg560d_environment *);
void syscon_application_event(uint8_t ram[4096],uint8_t event);
uint32_t syscon_application_count(const uint8_t ram[4096],uint32_t queue_address);
uint64_t syscon_application_helper(uint8_t ram[4096],const sg560d_environment *,
                                    uint32_t entry,uint32_t a0,uint32_t a1);
#endif
