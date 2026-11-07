#include "control_commands.h"
#include "rgb.h"
#include "syscon.h"
#include <string.h>
#include <setjmp.h>

static const char invalid[]="Invalid parameters. Use \"HELP:;\" for more details.";
static const char *const help_text[37];
static syscon_control_arg number(uint32_t value) {return (syscon_control_arg){0,value,0};}
static syscon_control_arg string(const char *value) {return (syscon_control_arg){1,0,value};}
static void print0(syscon_control_io *io,const char *fmt) {io->print(io->context,fmt,0,0);}
static void print1(syscon_control_io *io,const char *fmt,syscon_control_arg a) {io->print(io->context,fmt,&a,1);}
static int32_t call(syscon_control_io *io,uint32_t address,uint32_t a,uint32_t b,uint8_t *data,uint32_t size) {
    return io->call(io->context,address,a,b,data,size);
}
static int bad(syscon_control_io *io) {print0(io,invalid); return 0;}
static int equal(const char *a,const char *b) {return a && strcmp(a,b)==0;}
static int whitespace(unsigned char c) {return c==' ' || (c>=9 && c<=13);}
static int32_t decimal(const char *s,int *converted) {
    uint32_t value=0;
    int negative=0,overflow=0;
    while (whitespace((unsigned char)*s)) ++s;
    if (*s=='+' || *s=='-') negative=*s++=='-';
    *converted=0;
    const uint32_t limit=negative ? 0x80000000u : 0x7fffffffu;
    while (*s>='0' && *s<='9') {
        unsigned digit=(unsigned)(*s++-'0');
        *converted=1;
        if (value>limit/10 || (value==limit/10 && digit>limit%10)) overflow=1;
        if (!overflow) value=value*10+digit;
    }
    if (overflow) value=limit;
    return (int32_t)(negative ? 0u-value : value);
}

int32_t syscon_control_command(syscon_control_io *io,uint32_t handler,const char *args) {
    int converted;
    int32_t value,result;
    switch (handler) {
    case 0x3ef0:
        print1(io,"Version=%s",string("1.0.52")); return 1;
    case 0x3f24:
        print0(io,"Available commands:");
        for (unsigned i=0;i<37;++i) {
            syscon_control_arg a[]={string(syscon_commands[i].name),string(help_text[i])};
            io->print(io->context,"%s - %s",a,2);
        }
        return 1;
    case 0x3f80:
    case 0x47bc: {
        value=decimal(args,&converted);
        if (!converted) return bad(io);
        uint8_t pin_value=0;
        if (handler==0x3f80) {
            result=call(io,0x39e8,(uint32_t)value&255,0,&pin_value,1);
            if (result!=0) {print0(io,"IOEXP_READ Error");return 0;}
            result=pin_value;
        } else result=call(io,0x80f8,(uint32_t)value&65535,0,0,0);
        syscon_control_arg a[]={number((uint32_t)value),number((uint32_t)result)};
        io->print(io->context,"Pin %d value: %d",a,2);
        return 1;
    }
    case 0x3fd0:
        call(io,0x5358,0,0,0,0); return 1;
    case 0x40a0:
        if (!args) {
            value=call(io,0x6650,0,0,0,0);
            if (value<0) print0(io,"Timed wake: none");
            else print1(io,"Timed wake: in %ds",number((uint32_t)value));
            return 1;
        }
        value=decimal(args,&converted);
        if (!converted || (uint32_t)value>259200) return bad(io);
        call(io,0x65f0,(uint32_t)value,0,0,0);return 1;
    case 0x40fc:
        print0(io," MCU sleep");call(io,0x74f8,0,0,0,0);return 1;
    case 0x4110: {
        if (args && !equal(args,"HARD:;") && !equal(args,"SOFT:;")) return bad(io);
        int hard=equal(args,"HARD:;");
        syscon_control_arg a=string(hard ? "hard" : "soft");
        io->log(io->context,3,"MFGD","Reset MCU - %s",&a,1);
        if (hard) {call(io,0x37e4,0,0,0,0);call(io,0x5a88,0,0,0,0);}
        call(io,0x77c0,500,0,0,0);
        call(io,0xe000ed0c,0x05fa0004,0,0,0);
        return SYSCON_CONTROL_TERMINATED;
    }
    case 0x41a4:
        if (equal(args,"REBOOT:;")) value=1;
        else if (equal(args,"POWEROFF:;") || equal(args,"USER:;")) value=2;
        else if (equal(args,"BATTERY_LOW:;")) value=3;
        else if (equal(args,"THERMAL_HIGH:;")) value=4;
        else if (equal(args,"THERMAL_LOW:;")) value=5;
        else return bad(io);
        call(io,0x55dc,(uint32_t)value,0,0,0);return 1;
    case 0x422c: {
        /* Arguments supplied by the parser always include the two-byte suffix. */
        uint32_t length=(uint32_t)strlen(args)-2;
        call(io,0x74e8,0,length,(uint8_t *)(uintptr_t)args,length);
        uint8_t newline[2]={'\r','\n'};
        call(io,0x74e8,0,2,newline,2);return 1;
    }
    case 0x4258:
        if (equal(args,"NORMAL:;")) value=0x6428;
        else if (equal(args,"FASTBOOT:;")) value=0x65e4;
        else if (equal(args,"FCT:;")) value=0x65d0;
        else if (equal(args,"EDL:;")) value=0x64a0;
        else return bad(io);
        return call(io,(uint32_t)value,0,0,0,0)==0;
    case 0x42c8: {
        uint8_t config[6]={0};
        result=call(io,0x5dc8,0,0,config,6);
        if (result) {
            syscon_control_arg a[]={string(syscon_rgb_state_name(config[0])),number(config[1]),
                number(config[2]),number(config[3]),number(config[4]),string(syscon_rgb_pattern_name(config[5]))};
            io->print(io->context,"LEDSTATUS theme=%s red=%u green=%u blue=%u brightness=%u pattern=%s",a,6);
        }
        return result;
    }
    case 0x4320: {
        uint32_t state=(uint32_t)decimal(args,&converted);
        const char *colon=strchr(args,':');
        int32_t duration=colon ? decimal(colon+1,&converted) : 0;
        if (state>=10 || duration<0) return bad(io);
        return call(io,0x5c68,state&255,(uint32_t)duration,0,0)==0;
    }
    case 0x4364: {
        uint8_t config[5];
        static const char *const labels[]={"R: ","G: ","B: ","Brightness: ","Pattern: "};
        for (unsigned i=0;i<5;++i) {
            const char *colon=strchr(args,':');
            if (!colon || colon-args>3) return bad(io);
            char token[4];
            size_t n=(size_t)(colon-args);
            memcpy(token,args,n);token[n]=0;
            print0(io,labels[i]);print0(io,token);
            config[i]=(uint8_t)decimal(token,&converted);
            args=colon+1;
        }
        if (config[4]>=5) return bad(io);
        return call(io,0x5c38,0,0,config,5)==0;
    }
    case 0x4420: {
        static const char *const labels[]={"VPH: ","5V: ","VBAT: ","1V8: ","VUSB: "};
        for (unsigned i=0;i<5;++i) {
            result=call(io,0x4c50,12+i,0,0,0);
            syscon_control_arg a[]={string(labels[i]),number((uint32_t)result)};
            io->print(io->context,"%s: %dmV",a,2);
        }
        return 1;
    }
    case 0x47b0: call(io,0x5274,0,0,0,0);return 1;
    case 0x47fc:
        if (equal(args,"ON:;")) {io->debug_enabled=1;print0(io,"Debug enabled");}
        else if (equal(args,"OFF:;")) {io->debug_enabled=0;print0(io,"Debug disabled");}
        else return bad(io);
        return 1;
    case 0x4850:
        if (equal(args,"UP:;")) value=0x27;
        else if (equal(args,"DOWN:;")) value=0x1d;
        else if (equal(args,"POWER:;")) value=8;
        else return bad(io);
        call(io,0x7468,(uint32_t)value,0,0,0);return 1;
    case 0x48a4:
        if (equal(args,"SOFT:;")) value=0;
        else if (equal(args,"HARD:;")) value=1;
        else return bad(io);
        return call(io,0x6720,(uint32_t)value,0,0,0);
    case 0x48e0:
    case 0x49ac:
        if (*args!='0' && *args!='1') return bad(io);
        call(io,handler==0x48e0 ? 0x347c : 0x8fc0,(unsigned)(*args-'0'),0,0,0);return 1;
    case 0x4904:
        value=decimal(args,&converted);
        if (value==0) {
            uint8_t assertion[]="mfg_command.cpp\0" "0";
            call(io,0x2678,0x110,0,assertion,sizeof(assertion));
            return SYSCON_CONTROL_TERMINATED;
        }
        if (value==1) return 1;
        if (value==2) {
            syscon_control_arg a=number(0xffffffff);
            io->log(io->context,1,"MFGD","-1 failed: %d",&a,1);return 1;
        }
        io->log(io->context,1,"MFGD","Invalid error test command",0,0);return 0;
    case 0x4970:
        if (equal(args,"DETECT:;")) value=1;
        else if (equal(args,"PASSTHRU:;")) value=0;
        else return bad(io);
        call(io,0x591c,(uint32_t)value,0,0,0);return 1;
    default: return SYSCON_CONTROL_UNHANDLED;
    }
}

/* This bridge is host harness machinery, not reconstructed target code. */
typedef struct {
    jmp_buf stop;
    volatile int32_t *status;
    syscon_control_io *io;
    syscon_dispatch fallback;
    void *fallback_context;
    syscon_echo echo;
    void *echo_context;
} control_frame;

static int control_dispatch(void *context,uint32_t handler,const char *args) {
    control_frame *frame=context;
    int32_t result=syscon_control_command(frame->io,handler,args);
    if (result==SYSCON_CONTROL_UNHANDLED && frame->fallback)
        result=frame->fallback(frame->fallback_context,handler,args);
    if (result==SYSCON_CONTROL_TERMINATED || result==SYSCON_CONTROL_UNHANDLED) {
        *frame->status=result;
        longjmp(frame->stop,1);
    }
    return result;
}
static void control_print(void *context,const char *text) {
    control_frame *frame=context;
    print0(frame->io,text);
}
static void control_echo(void *context,uint8_t byte) {
    control_frame *frame=context;
    if (frame->echo) frame->echo(frame->echo_context,byte);
}
int32_t syscon_control_feed(syscon_control_io *io,syscon_parser *parser,const uint8_t *data,size_t length,
                            syscon_dispatch fallback,void *fallback_context,syscon_echo echo,void *echo_context) {
    volatile int32_t status=0;
    control_frame frame={.status=&status,.io=io,.fallback=fallback,.fallback_context=fallback_context,
                         .echo=echo,.echo_context=echo_context};
    if (setjmp(frame.stop)==0)
        syscon_parser_feed(parser,data,length,control_dispatch,control_print,control_echo,&frame);
    return status;
}

/* HELP text is appended below from the pinned firmware's packed command table. */

static const char *const help_text[37] = {
    "Displays a list of available commands ( HELP:; )",
    "Checks if battery is present ( BATCHECK:; )",
    "Test error handling ( ERROR:<[0,1,2]>:; )",
    "Enables/disables logging ( LOG:<[0,1]>:; )",
    "Enables/disables diagnostic ( DIAG:<[0,1]>:; )",
    "Displays MCU firmware version ( VERSION:; )",
    "Sets configuration values ( CONFIG_SET:<key>:<value>:; )",
    "Gets configuration values ( CONFIG_GET:<key>:; )",
    "Finds configuration values ( CONFIG_FIND:<key>:; )",
    "Erases all configuration values ( CONFIG_ERASE:<password>:; )",
    "Dumps all configuration values ( CONFIG_DUMP:; )",
    "Sets configuration values ( CONFIG_ID_SET:<key>:<value>:; )",
    "Gets configuration values ( CONFIG_ID_GET:<key>:; )",
    "Finds configuration values ( CONFIG_ID_FIND:<key>:; )",
    "Erases all configuration values ( CONFIG_ID_ERASE:<password>:; )",
    "Dump all configuration values ( CONFIG_ID_DUMP:; )",
    "Reads power status ( READ_PWR:; )",
    "Sets RGB values ( SET_RGB:<r>:<g>:<b>:<brightness>:<pattern>:; )",
    "Sets RGB pattern ( SET_PATTERN:<pattern>:<ms>:; )",
    "Gets the current LED theme, color, brightness, and pattern ( LEDSTATUS:; )",
    "Sets PWR key mode ( KEY_MODE:<[DETECT,PASSTHRU]>:; )",
    "Powers on SG560D ( 560D_ON:<[NORMAL,FASTBOOT,FCT,EDL]>:; )",
    "Powers on SG560D ( 560D_ON/POWER:<[NORMAL,FASTBOOT,FCT,EDL]>:; )",
    "Powers off SG560D ( 560D_OFF:<[SOFT,HARD]>:; )",
    "Forward payload to SG560D ( 560D_DIRECT:<payload>:; )",
    "Enables/Disables debug for SG560D ( 560D_DBG:<[ON,OFF]>:; )",
    "Sets shutdown reason ( SHUTDOWN_REASON:<[REBOOT,POWEROFF,BATTERY_LOW,THERMAL_HIGH,THERMAL_LOW]>:; )",
    "Reboots the MCU ( MCU_REBOOT/REBOOT:<optional HARD|SOFT>:; )",
    "Reboots the MCU ( MCU_REBOOT/REBOOT:<optional HARD|SOFT>:; )",
    "Makes the MCU enter sleep mode ( MCU_SLEEP:; )",
    "Powers on after N seconds, 0 cancels, no arg reports ( WAKE_AFTER:<optional seconds>:; )",
    "Gets the non-volatile data ( CONFIG_INTERNAL:; )",
    "Control MCU keys ( KEYS:<[up,down,power]>:; )",
    "Gets the current power status ( PWRSTATUS:; )",
    "Gets the current power status ( STATUS:; )",
    "Gets an IO expander pin value ( IOEXP_READ:<pin>:; )",
    "Gets a MCU GPIO pin value ( GPIO_READ:<pin>:; )",
};
