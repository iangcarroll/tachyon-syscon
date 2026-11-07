"""Bounded application init/loop execution; hardware remains explicit hooks."""
from oracle import Oracle
from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_PC,UC_ARM_REG_R1

DEPENDENCIES={0x798c:0,0x7b88:0,0x7b78:1,0x7be0:0,0x8fc0:1,0x59d8:0,
    0x776c:0,0x7540:0,0x79d0:0,0x30f0:0,0x7910:0,0x5b7c:1,0x7c08:0,
    0x5afc:0,0x5970:1,0x5908:2,0x3808:1,0x7c3c:1,0x7bfc:0,0x7b9c:1,
    0x5ac4:0,0x66a0:1,0x5af0:0,0x5b14:0,0x54cc:1,0x6948:1,0x4c24:0,
    0x3114:0,0x3144:0,0x5c68:1,0x6428:0,0x7a50:0,0x77b4:0,0x969c:3,
    0x3488:0,0x3138:0,0x6690:0,0x5e24:0,0x64a0:0,0x65e4:0,0x4c14:0,
    0x6a68:0,0x75d8:0,0x76d8:0,0x6720:1,0x7974:0,0x51c0:0,0x49d0:1,
    0x8c8c:3}
DEPENDENCIES.update({0x3120:0,0x8148:4,0x81f8:1,0x77fc:1,0x80f8:1})


class ApplicationOracle(Oracle):
    def __init__(self,respond):
        super().__init__()
        self.events=[];self.respond=respond
        self.hooks[0x8f88]=lambda _:None
        for address,count in DEPENDENCIES.items():
            self.hooks[address]=lambda o,address=address,count=count:self._dependency(address,count)
        self.hooks[0x8954]=self._uart
        self.hooks[0x7f58]=self._gpio
        self.cpu.reg_write(UC_ARM_REG_SP,0x20000fc0)

    def _dependency(self,address,count):
        args=tuple(self.arg(i) for i in range(count));self.events.append((address,args,b''))
        result=self.respond(address,args)
        if address==0x77b4:self.cpu.reg_write(UC_ARM_REG_R1,(result>>32)&0xffffffff)
        return result&0xffffffff

    def _uart(self,o):
        args=(self.arg(0),);data=bytes(self.cpu.mem_read(self.arg(1),9))
        self.events.append((0x8954,args,data));return self.respond(0x8954,args)&0xffffffff

    def _gpio(self,o):
        args=(self.arg(0),);data=bytes(self.cpu.mem_read(self.arg(1),12))
        self.events.append((0x7f58,args,data));return self.respond(0x7f58,args)&0xffffffff

    def run_init(self):
        self.cpu.reg_write(UC_ARM_REG_SP,0x20000ff0)
        self.cpu.emu_start(0x3b35,0x3c9a,count=200000)
        assert self.cpu.reg_read(UC_ARM_REG_PC)==0x3c9a

    def run_tick(self):
        # Execute one loop body, then its back-edge, stopping at the next entry.
        self.cpu.ctl_remove_cache(0x3c9a,0x3da8)
        self.cpu.emu_start(0x3c9b,0x3da6,count=200000)
        assert self.cpu.reg_read(UC_ARM_REG_PC)==0x3da6
        # Remove the translation-block stop inserted by the preceding `until`.
        self.cpu.ctl_remove_cache(0x3da6,0x3da8)
        self.cpu.emu_start(0x3da7,self.SENTINEL,count=1)
        assert self.cpu.reg_read(UC_ARM_REG_PC)==0x3c9a
