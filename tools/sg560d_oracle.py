"""SG560D instruction oracle with typed external dependency traces."""
from oracle import Oracle
from unicorn.arm_const import UC_ARM_REG_R1

DEPENDENCIES={0x77b4:0,0x7d54:0,0x55dc:1,0x6282:0,0x7928:1,
    0x5aa8:1,0x5c68:1,0x591c:1,0x76d8:0,0x4c50:1,0x5048:1,
    0x4e34:1,0x3150:0,0x4fd0:0,0x4ee0:1,0x4ed4:1,0x5e30:0,
    0x6248:0,0x8054:2,0x5f30:0,0x364e:2,0x614c:0,0x77c0:1}
DEPENDENCIES.update({0x5694:0,0x559c:0,0x55b4:0,0x4ca8:0,0x562c:0,
    0x5670:0,0x567c:0,0x55c4:0,0x80f8:1,0x5dbc:0,0x49d0:1,
    0x3114:0,0x517c:0,0x5638:0})
DEPENDENCIES.update({0x8b50:1,0x5274:0,0x3194:0,0x4d9c:0,0x5358:1,0x2678:3})
PAYLOADS={0x7f58:12,0x386c:3,0x8954:9}


class SG560DOracle(Oracle):
    def __init__(self,respond):
        super().__init__()
        self.events=[]
        self.respond=respond
        self.hooks[0x8f88]=lambda _:None
        for address,count in DEPENDENCIES.items():
            self.hooks[address]=lambda o,address=address,count=count:self._dependency(address,count)
        self.hooks[0x7554]=self._tasks
        for address,length in PAYLOADS.items():
            self.hooks[address]=lambda o,address=address,length=length:self._payload(address,length)

    def _dependency(self,address,count):
        args=tuple(self.arg(i) for i in range(count))
        self.events.append((address,args,b''))
        value=self.respond(address,args)
        if address in (0x77b4,0x5638):self.cpu.reg_write(UC_ARM_REG_R1,value>>32)
        return value&0xffffffff

    def _tasks(self,o):
        count=self.arg(1)
        data=bytes(self.cpu.mem_read(self.arg(0),count*8))
        self.events.append((0x7554,(count,),data))
        return self.respond(0x7554,(count,))

    def _payload(self,address,length):
        args=(self.arg(0),)
        data=bytes(self.cpu.mem_read(self.arg(1),length))
        self.events.append((address,args,data))
        return self.respond(address,args)&0xffffffff
