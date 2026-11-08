#include "flash_controller.h"
static uint32_t word(const uint8_t *p) {return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
uint32_t syscon_flash_execute(const syscon_flash_controller_io *io,uint32_t base) {
    io->write(io->context,base+0x1100,1);
    uint32_t status;
    do {status=io->read(io->context,base+0x13d0)&7;} while (status!=1 && status!=3);
    return status;
}
uint32_t syscon_flash_erase(const syscon_flash_controller_io *io,uint32_t base,uint32_t address,uint32_t size) {
    io->write(io->context,base+0x1104,size|2);
    io->write(io->context,base+0x1120,address);
    return syscon_flash_execute(io,base);
}
uint32_t syscon_flash_program(const syscon_flash_controller_io *io,uint32_t base,uint32_t address,const uint8_t data[8]) {
    io->write(io->context,base+0x1104,1);
    io->write(io->context,base+0x1124,0xff);
    io->write(io->context,base+0x1120,address);
    io->write(io->context,base+0x1130,word(data));
    io->write(io->context,base+0x1134,word(data+4));
    return syscon_flash_execute(io,base);
}
uint32_t syscon_flash_blank(const syscon_flash_controller_io *io,uint32_t base,uint32_t address) {
    io->write(io->context,base+0x1104,6);
    io->write(io->context,base+0x1120,address);
    return syscon_flash_execute(io,base);
}
void syscon_flash_unprotect_main(const syscon_flash_controller_io *io,uint32_t base) {
    io->write(io->context,base+0x11d0,0);
    io->write(io->context,base+0x11d4,0);
    io->write(io->context,base+0x11d8,0);
}
void syscon_flash_report(const syscon_flash_controller_io *io,uint32_t base,syscon_flash_reporter report,void *context) {
    const char *message;
    switch (io->read(io->context,base+0x13d0)&0x10f0) {
    case 0:message="Flash: op success";break;
    case 0x10:message="Flash: write/erase protect failure";break;
    case 0x20:message="Flash: verify error failure";break;
    case 0x40:message="Flash: illegal address failure";break;
    case 0x80:message="Flash: wrong bank mode failure";break;
    case 0x1000:message="Flash: undefined failure";break;
    default:message="Flash: unknown failure";break;
    }
    report(context,1,"CONF",message);
}
