"""Run original command parsing and real non-config command handlers.

Subsystems are explicit scripted dependencies. The original integer parsing,
argument checks, formatting call sites and handler control flow all execute.
"""
import re
import struct
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_LR
from oracle import Oracle


class ControlTerminated(Exception):
    pass


class ControlDependencies:
    def __init__(self,results=None):
        self.events=[]
        self.results=results or {}
        self.outputs={0x39e8:b'\x01',0x5dc8:bytes([5,12,34,56,78,1])}
        self.forwarded_status=[('power fixture: %d',(1234,))]

    def call(self,address,a=0,b=0,data=None,size=0):
        incoming=bytes(data) if address in (0x5c38,0x74e8,0x2678) else None
        self.events.append(('call',address,a,b,incoming,size))
        if address==0x5358:
            for fmt,args in self.forwarded_status: self.events.append(('print',fmt,args))
        return self.results.get(address,0)


class ControlOracle(Oracle):
    PRINT=0x10010
    CONTEXT=0x20000048
    BUFFER=0x20000300
    DEBUG=0x200002ee
    ARGUMENT=0x20000900
    NOARGS=(0x5358,0x6650,0x74f8,0x37e4,0x5a88,0x6428,0x65e4,0x65d0,0x64a0,0x5274)
    ONEARG=(0x65f0,0x77c0,0x55dc,0x4c50,0x7468,0x6720,0x347c,0x8fc0,0x591c,0x80f8)

    def __init__(self,deps,debug=0):
        super().__init__()
        self.deps=deps
        self.pending=bytearray()
        self.put(self.DEBUG,bytes([debug]))
        self.put(self.CONTEXT,struct.pack('<B3xIIBB2xI',0,self.BUFFER,0,0,1,self.PRINT|1))
        self.hooks[self.PRINT]=self._print
        self.hooks[0x8f88]=self._log
        self.hooks[0x2678]=self._assertion
        self.hooks[0x8cf0]=lambda _:len(self.pending)
        self.hooks[0x8de4]=lambda _:self.pending.pop(0)
        for address in self.NOARGS:
            self.hooks[address]=lambda o,address=address:self.deps.call(address)
        for address in self.ONEARG:
            self.hooks[address]=lambda o,address=address:self.deps.call(address,o.arg(0))
        self.hooks[0x39e8]=self._pin_read
        self.hooks[0x5dc8]=self._led_read
        self.hooks[0x5c38]=self._led_config
        self.hooks[0x5c68]=lambda o:self.deps.call(0x5c68,o.arg(0),o.arg(1))
        self.hooks[0x74e8]=self._direct
        self.cpu.mem_map(0xe000e000,0x1000)
        self.cpu.hook_add(UC_HOOK_MEM_WRITE,self._system_write,begin=0xe000ed0c,end=0xe000ed0f)

    def format_args(self,fmt,offset=1):
        types=re.findall(r'%(?:[-+ #0]*\d*)?([sdu])',fmt)
        args=[]
        for i,kind in enumerate(types,offset):
            value=self.arg(i)
            if kind=='s': value=self.cstring(value).decode('latin1')
            args.append(value)
        return tuple(args)

    def _print(self,o):
        fmt=o.cstring(o.arg(0)).decode('latin1')
        # Original SET_RGB passes the user token as a format with NO arguments.
        # Its actual variadic rendering is undefined for conversion specifiers.
        token_call=(o.cpu.reg_read(UC_ARM_REG_LR)&~1)==0x43cc
        self.deps.events.append(('print',fmt,() if token_call else self.format_args(fmt)))

    def _log(self,o):
        caller=o.cpu.reg_read(UC_ARM_REG_LR)&~1
        if 0x49d0<=caller<0x4c14: return # Parser's separate diagnostic side channel.
        fmt=o.cstring(o.arg(2)).decode('latin1')
        self.deps.events.append(('log',o.arg(0),o.cstring(o.arg(1)).decode('latin1'),fmt,self.format_args(fmt,3)))

    def _assertion(self,o):
        data=o.cstring(o.arg(0))+b'\0'+o.cstring(o.arg(2))+b'\0'
        self.deps.call(0x2678,o.arg(1),0,data,len(data))
        raise ControlTerminated()

    def _system_write(self,uc,access,address,size,value,_):
        self.deps.call(address,value)
        raise ControlTerminated()

    def _pin_read(self,o):
        result=self.deps.call(0x39e8,o.arg(0),0,None,1)
        o.put(o.arg(1),self.deps.outputs[0x39e8])
        return result

    def _led_read(self,o):
        result=self.deps.call(0x5dc8,0,0,None,6)
        o.put(o.arg(0),self.deps.outputs[0x5dc8])
        return result

    def _led_config(self,o):
        data=bytes(o.cpu.mem_read(o.arg(0),5))
        return self.deps.call(0x5c38,0,0,data,5)

    def _direct(self,o):
        count=o.arg(1)
        if count>128: raise ValueError('Invalid direct-handler input outside parser contract')
        return self.deps.call(0x74e8,0,count,bytes(o.cpu.mem_read(o.arg(0),count)),count)

    def invoke(self,address,args):
        if args is not None: self.put(self.ARGUMENT,args+b'\0')
        try: return self.call(address,self.ARGUMENT if args is not None else 0,self.PRINT|1)
        except ControlTerminated: return 0x80000000

    def feed(self,data):
        self.pending.extend(data)
        try: self.call(0x49d0,self.CONTEXT)
        except ControlTerminated: return False
        return True
