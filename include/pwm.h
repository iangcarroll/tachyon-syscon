#ifndef SYSCON_PWM_H
#define SYSCON_PWM_H
#include <stdint.h>
typedef struct {uint8_t pin,mux,pad0[2];uint32_t base;uint8_t compare,pad1[3];} syscon_pwm_channel;
typedef struct {uint32_t base;uint8_t gpio,pincm,pad[2];} syscon_pwm_pin;
typedef struct {syscon_pwm_channel channels[3];syscon_pwm_pin pins[25];} syscon_pwm_board;
typedef struct {uint32_t period;uint8_t mode,extra_channels,control,padding;} syscon_pwm_config;
typedef struct {
    void *context;
    uint32_t (*read)(void *,uint32_t);
    void (*write)(void *,uint32_t,uint32_t);
    void (*assertion)(void *,unsigned);
} syscon_pwm_io;
void syscon_pwm_default_board(syscon_pwm_board *);
int syscon_pwm_init(const syscon_pwm_board *,const syscon_pwm_io *,unsigned pin);
int syscon_pwm_write(const syscon_pwm_board *,const syscon_pwm_io *,unsigned pin,uint32_t value);
void syscon_pwm_clock(const syscon_pwm_io *,uint32_t base,const uint8_t config[3]);
void syscon_pwm_compare(const syscon_pwm_io *,uint32_t base,uint32_t value,unsigned index);
void syscon_pwm_capture(const syscon_pwm_io *,uint32_t base,uint32_t a,uint32_t b,unsigned index);
void syscon_pwm_action(const syscon_pwm_io *,uint32_t base,uint32_t value,unsigned index);
void syscon_pwm_output(const syscon_pwm_io *,uint32_t base,uint32_t a,uint32_t b,unsigned index);
void syscon_pwm_configure(const syscon_pwm_io *,uint32_t base,const syscon_pwm_config *);
#endif
