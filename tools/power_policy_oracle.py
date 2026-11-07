"""Power status/report policy oracle with explicit peripheral/dependency calls."""
import re
import struct
from oracle import Oracle
from unicorn.arm_const import UC_ARM_REG_R1

DEPENDENCIES={0x4c50:1,0x4ca8:0,0x5af0:0,0x4d00:0,0x4d9c:0,
              0x4d58:0,0x4df4:0,0x3620:1,0x4ec4:0,0x77b4:0}

class PowerPolicyOracle(Oracle):
    PRINT=0x10010
    def __init__(self,respond):
        super().__init__()
        self.respond=respond;self.events=[]
        self.hooks[0x8f88]=lambda _:None
        for address,n in DEPENDENCIES.items():
            self.hooks[address]=lambda o,address=address,n=n:self.dependency(address,n)
        self.hooks[0x7c54]=lambda o:self.payload(0x7c54,7)
        self.hooks[0x386c]=lambda o:self.payload(0x386c,3)
        for address in [self.PRINT,0x8fa0]:
            self.hooks[address]=lambda o,address=address:self.print_callback(address)

    def dependency(self,address,n):
        args=tuple(self.arg(i) for i in range(n))
        self.events.append((address,args,b''))
        result=self.respond(address,args)
        if address==0x77b4:self.cpu.reg_write(UC_ARM_REG_R1,result>>32)
        return result&0xffffffff

    def payload(self,address,length):
        data=bytes(self.cpu.mem_read(self.arg(1),length))
        args=(self.arg(0),)
        self.events.append((address,args,data))
        return self.respond(address,args)&0xffffffff

    def print_callback(self,address):
        fmt=self.arg(0)
        count=len(re.findall(rb'%[sdu]',self.cstring(fmt)))
        payload=b''.join(struct.pack('<I',self.arg(i+1)) for i in range(count))
        self.events.append((address,(fmt,count),payload))
        return 0
