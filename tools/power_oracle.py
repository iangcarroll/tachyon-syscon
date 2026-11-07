"""Original power-routing algorithms with explicit ADC/GPIO/time/task endpoints."""
import struct
from unicorn.arm_const import UC_ARM_REG_R1
from oracle import Oracle

class PowerAssertion(Exception): pass

class PowerEnvironment:
    def __init__(self):
        self.gpio={i:0 for i in range(256)}
        self.adc={i:[1500] for i in range(256)}
        self.stuck=set();self.write_result=0;self.now=0;self.task_result=0
        self.trace=[]
    def call(self,address,a=0,b=0,payload=b''):
        self.trace.append((address,a,b,payload))
        if address==0x3620:return self.gpio[a]
        if address==0x364e:
            if a not in self.stuck:self.gpio[a]=b
            return self.write_result&0xffffffff
        if address==0x7f24:
            samples=self.adc.get(a,[0])
            return samples.pop(0) if len(samples)>1 else samples[0]
        if address==0x77b4:return self.now
        if address==0x7554:return self.task_result&0xffffffff
        return 0

class PowerOracle(Oracle):
    def __init__(self):
        super().__init__();self.env=PowerEnvironment()
        for address,count in {0x3620:1,0x364e:2,0x7f24:1,0x77c0:1,0x5ad4:1}.items():
            self.hooks[address]=lambda o,a=address,c=count:self.env.call(a,o.arg(0),o.arg(1) if c>1 else 0)
        def now(o):
            value=self.env.call(0x77b4);o.cpu.reg_write(UC_ARM_REG_R1,value>>32);return value&0xffffffff
        self.hooks[0x77b4]=now
        self.hooks[0x7554]=lambda o:self.env.call(0x7554,0,o.arg(1),bytes(o.cpu.mem_read(o.arg(0),o.arg(1)*8)))
        self.hooks[0x8f88]=lambda _:None
        def assertion(o):
            self.env.call(0x2678,o.arg(1));raise PowerAssertion(o.arg(1))
        self.hooks[0x2678]=assertion
