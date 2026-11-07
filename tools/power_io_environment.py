"""Power/expander/I2C integration at the MMIO and external-device boundary.

The peripheral model implements only the explicitly exercised synchronous I2C
features. It is not a complete MSPM0 or analog/electrical emulator.
"""
import collections
import ctypes as C
import struct
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_R1
from oracle import Oracle
from i2c_oracle import BASE,REGISTERS
from adc_oracle import ADC,REGISTERS as ADC_REGISTERS


class IntegrationAssertion(Exception):pass


class PowerIoPeripheral:
    def __init__(self,expander,mmio,*,stuck_low=0):
        assert len(expander)==8
        self.expander=bytearray(expander)
        self.mmio=dict(mmio)
        self.stuck_low=stuck_low
        self.events=[];self.pointer=0
        self.tx=collections.deque();self.rx=collections.deque()
        self.active=None;self.pending_irqs=collections.deque()
        self.failures=collections.deque()
        self.read_scripts={}
        self.now=1000

    def read_device(self):
        reg=self.pointer
        if reg<2:
            direction=self.expander[6+reg]
            value=((self.expander[reg]&direction)|(self.expander[reg+2]&(~direction&255)))^self.expander[reg+4]
        else:value=self.expander[reg]
        self.pointer=(reg&6)|((reg+1)&1)
        return value

    def write_device(self,frame):
        self.pointer=frame[0]&7
        for value in frame[1:]:
            reg=self.pointer
            if reg>=2:
                if reg in (2,3):value&=~((self.stuck_low>>(8*(reg-2)))&255)
                self.expander[reg]=value
            self.pointer=(reg&6)|((reg+1)&1)

    def complete_tx(self):
        t=self.active
        if t and not t['read']:
            while self.tx and len(t['bytes'])<t['count']:t['bytes'].append(self.tx.popleft())
            if len(t['bytes'])==t['count'] and not t['committed']:
                t['committed']=True
                if not t['nack']:
                    self.events.append(('wire-write',t['address'],bytes(t['bytes'])))
                    if t['bytes']:self.write_device(t['bytes'])

    def start(self,control):
        address=(self.mmio[BASE+0x1210]&0x7ff)>>1
        reading=bool(self.mmio[BASE+0x1210]&1)
        count=(control>>16)&0xfff
        failure=self.failures.popleft() if self.failures else None
        nack=failure=='nack' or address!=0x26
        self.events.append(('wire-start',address,'read' if reading else 'write',count,nack))
        self.active=dict(address=address,read=reading,count=count,nack=nack,busy_seen=False,bytes=bytearray(),committed=False)
        if nack:
            if self.mmio[BASE+0x1028]&0x80 and self.mmio[0xe000e100]&(1<<24):self.pending_irqs.append(8)
        elif reading:
            values=bytes(self.read_device() for _ in range(count))
            self.rx.extend(values)
            self.events.append(('wire-read',address,values))
        self.complete_tx()

    def read(self,address):
        scripted=self.read_scripts.get(address)
        if scripted:value=scripted.popleft()
        elif address==BASE+0x1218:
            t=self.active
            if not t:value=0x20
            elif not t['busy_seen']:t['busy_seen']=True;value=0x40
            elif t['nack'] or (t['read'] and not self.rx) or (not t['read'] and t['committed']):
                self.events.append(('wire-stop',t['address']))
                self.active=None;value=0x20
            else:value=0x40
        elif address==BASE+0x123c:value=((8-len(self.tx))<<8)|min(len(self.rx),15)
        elif address==BASE+0x121c:
            if not self.rx:raise AssertionError('RX FIFO underflow')
            value=self.rx.popleft()
        else:
            if address not in self.mmio:raise AssertionError(f'Unprovided MMIO {address:#x}')
            value=self.mmio[address]
        self.events.append(('read',address,value))
        return value

    def write(self,address,value):
        self.events.append(('write',address,value));self.mmio[address]=value
        if address==BASE+0x1220:
            if len(self.tx)>=8:raise AssertionError('TX FIFO overflow')
            self.tx.append(value&255);self.complete_tx()
        elif address==BASE+0x1214:
            if value&7==7:self.start(value)
            elif value==0:self.active=None
        elif address==BASE+0x1238:
            if value&0x80:self.tx.clear()
            if value&0x8000:self.rx.clear()

    def irq_enter(self):
        reason=self.pending_irqs.popleft();self.mmio[BASE+0x1020]=reason
        self.events.append(('irq-enter',reason))

    def irq_exit(self):self.events.append(('irq-exit',))
    def cycles(self,value):self.events.append(('cycles',value))
    def assertion(self,line):self.events.append(('assert',line))
    def invalid(self,pin):self.events.append(('invalid-output',pin))

    def dependency(self,address,a=0,b=0,payload=b''):
        if address not in [0x77b4,0x77c0,0x5ad4,0x7554]:
            raise AssertionError(f'Unexpected dependency boundary {address:#x}')
        self.events.append(('dependency',address,a,b,payload))
        if address==0x77b4:return self.now
        if address==0x77c0:self.now+=a
        return 0


def explicit_mmio_state():
    # Test fixture values, explicitly provided; these are not claimed reset values.
    state={address:0 for address in REGISTERS+ADC_REGISTERS}
    state[BASE+0x1028]=0x480
    state[0xe000e100]=1<<24
    state[ADC+0x556280]=3000 # Explicit input sample, not a silicon reset value.
    return state


class PowerIoOracle(Oracle):
    IRQ_RETURN=0x10060
    DATA=0x20000900
    def __init__(self,model):
        self.model=model;self.irq_context=None
        super().__init__()
        for page in {address&~0xfff for address in model.mmio}:self.cpu.mem_map(page,0x1000)
        self.cpu.hook_add(UC_HOOK_MEM_READ,self._read,begin=0x40000000,end=0xffffffff)
        self.cpu.hook_add(UC_HOOK_MEM_WRITE,self._write,begin=0x40000000,end=0xffffffff)
        self.hooks[0x7ae8]=lambda o:self.model.cycles(o.arg(0))
        self.hooks[0x2678]=self._assertion
        self.hooks[0x8f88]=self._log
        for address in [0x77c0,0x5ad4]:
            self.hooks[address]=lambda o,address=address:self.model.dependency(address,o.arg(0))
        def clock(o):
            value=self.model.dependency(0x77b4);o.cpu.reg_write(UC_ARM_REG_R1,value>>32);return value&0xffffffff
        self.hooks[0x77b4]=clock
        self.hooks[0x7554]=lambda o:self.model.dependency(0x7554,0,o.arg(1),bytes(o.cpu.mem_read(o.arg(0),o.arg(1)*8)))
        # No hooks on power policy, GPIO routing, expander, I2C HAL, or ADC HAL.

    def _step(self,uc,address,size,user):
        if address==self.IRQ_RETURN:
            resume=self.irq_resume
            uc.context_restore(self.irq_context);self.irq_context=None;self.model.irq_exit()
            # context_restore alone does not invalidate Unicorn's current TB.
            uc.reg_write(UC_ARM_REG_PC,resume|1);return
        if self.model.pending_irqs and self.irq_context is None:
            self.irq_resume=address;self.irq_context=uc.context_save();self.model.irq_enter()
            uc.reg_write(UC_ARM_REG_LR,self.IRQ_RETURN|1);uc.reg_write(UC_ARM_REG_PC,0x8799);return
        super()._step(uc,address,size,user)

    def _read(self,uc,access,address,size,value,user):
        assert size==4
        uc.mem_write(address,struct.pack('<I',self.model.read(address)))
    def _write(self,uc,access,address,size,value,user):
        assert size==4;self.model.write(address,value)
    def _assertion(self,o):
        self.model.assertion(o.arg(1));raise IntegrationAssertion(o.arg(1))
    def _log(self,o):
        if o.cstring(o.arg(2))==b'IOExpander[P%d]: input, invalid op':self.model.invalid(o.arg(3))
    def invoke(self,entry,*args):
        try:return self.call(entry,*args,count=3000000)
        except IntegrationAssertion:return -2


READ=C.CFUNCTYPE(C.c_uint32,C.c_void_p,C.c_uint32)
WRITE=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32,C.c_uint32)
SIGNAL=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32)
class I2cEnvironment(C.Structure):
    _fields_=[('read',READ),('write',WRITE),('delay',SIGNAL),('assertion',SIGNAL),('ctx',C.c_void_p)]
INIT=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint,C.c_void_p)
TRANSFER=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint,C.c_uint,C.c_void_p,C.c_uint)
GPIO_READ=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint)
GPIO_WRITE=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_uint)
class IoContext(C.Structure):
    _fields_=[('context',C.c_void_p),('init',INIT),('write',TRANSFER),('read',TRANSFER),
        ('assertion',SIGNAL),('invalid',SIGNAL),('gpio_read',GPIO_READ),('gpio_write',GPIO_WRITE),('initialized',C.c_uint8)]
POWER_CALL=C.CFUNCTYPE(C.c_uint64,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint32)
class PowerEnvironment(C.Structure):
    _fields_=[('call',POWER_CALL),('ctx',C.c_void_p)]


class NativePowerIo:
    def __init__(self,lib,model,ram):
        self.lib=lib;self.model=model;self.ram=C.create_string_buffer(ram,4096)
        self.faulted=False;self.in_irq=False
        lib.syscon_i2c_execute.argtypes=[C.c_void_p,C.POINTER(I2cEnvironment),C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint32]
        lib.syscon_i2c_execute.restype=C.c_uint64
        lib.syscon_power_execute.argtypes=[C.c_void_p,C.POINTER(PowerEnvironment),C.c_uint32,C.c_uint32]
        lib.syscon_power_execute.restype=C.c_uint64
        lib.syscon_adc_execute.argtypes=[C.c_void_p,C.POINTER(I2cEnvironment),C.c_uint32,C.c_uint32,C.c_void_p]
        lib.syscon_adc_execute.restype=C.c_uint64
        self.mmio_callbacks=[READ(self._read),WRITE(self._write),SIGNAL(lambda _,n:model.cycles(n)),SIGNAL(self._assertion)]
        self.mmio_env=I2cEnvironment(*self.mmio_callbacks,None)
        self.io_callbacks=[INIT(lambda _,bus,cfg:self._i2c(0x82f0,bus,0,cfg,8)),
            TRANSFER(lambda _,bus,address,data,count:self._i2c(0x844c,bus,address,data,count)),
            TRANSFER(lambda _,bus,address,data,count:self._i2c(0x860c,bus,address,data,count)),
            SIGNAL(self._assertion),SIGNAL(lambda _,pin:model.invalid(pin)),
            GPIO_READ(self._unsupported_gpio_read),GPIO_WRITE(self._unsupported_gpio_write)]
        self.io=IoContext(None,*self.io_callbacks,ram[0x2d0])
        self.power_callback=POWER_CALL(self._power_dependency)
        self.power_env=PowerEnvironment(self.power_callback,None)

    def _drain_irq(self):
        if self.model.pending_irqs and not self.in_irq:
            self.in_irq=True;self.model.irq_enter()
            self.lib.syscon_i2c_execute(self.ram,C.byref(self.mmio_env),0x8798,0,0,None,0)
            self.model.irq_exit();self.in_irq=False
    def _read(self,_,address):
        value=self.model.read(address);self._drain_irq();return value
    def _write(self,_,address,value):self.model.write(address,value);self._drain_irq()
    def _assertion(self,_,line):self.faulted=True;self.model.assertion(line)
    def _unsupported_gpio_read(self,_,pin):raise AssertionError(f'Direct GPIO pin{pin} outside this integration')
    def _unsupported_gpio_write(self,_,pin,value):raise AssertionError(f'Direct GPIO pin{pin} outside this integration')
    def _i2c(self,entry,bus,address,data,count):
        value=self.lib.syscon_i2c_execute(self.ram,C.byref(self.mmio_env),entry,bus,address,data,count)
        if value==0xffffffffffffffff:return -2 # Nonreturning original assertion.
        return C.c_int32(value&0xffffffff).value
    def _sync_initialized(self):C.memmove(C.addressof(self.ram)+0x2d0,bytes([self.io.initialized]),1)
    def _power_dependency(self,_,address,a,b,payload,size):
        if address==0x7f24:return self.lib.syscon_adc_execute(self.ram,C.byref(self.mmio_env),address,a,None)
        if address==0x3620:return self.lib.syscon_gpio_read(C.byref(self.io),a)&0xffffffffffffffff
        if address==0x364e:return self.lib.syscon_gpio_write(C.byref(self.io),a,b)&0xffffffffffffffff
        if address==0x2678:self._assertion(None,a);return 0
        return self.model.dependency(address,a,b,C.string_at(payload,size) if size else b'')&0xffffffffffffffff
    def io_call(self,name,*args):
        self.faulted=False
        result=getattr(self.lib,name)(C.byref(self.io),*args)
        self._sync_initialized();return -2 if self.faulted else result
    def adc_init(self,pin,config):
        return self.lib.syscon_adc_execute(self.ram,C.byref(self.mmio_env),0x7c54,pin,C.c_char_p(config))
    def power(self,entry,a=0):
        self.faulted=False
        result=self.lib.syscon_power_execute(self.ram,C.byref(self.power_env),entry,a)
        self._sync_initialized();return -2 if self.faulted else result
