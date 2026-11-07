"""Explicit digital peripheral model, checked against the pinned TI headers.

Ticks are emulator instructions, not silicon clock cycles. UART transmission is
an immediate external sink; ADC/WWDT delays are configurable virtual timing.
Unsupported analog/clock/boot-ROM behavior is not inferred from SVD presence.
"""
from collections import deque
from unicorn.arm_const import UC_ARM_REG_PC
from .core import BusFault, ModelError, UnsupportedRegister
from .profile import IRQ
from flash_controller_oracle import FlashControllerModel
from power_io_environment import PowerIoPeripheral

class MissingInput(ModelError): pass

class Devices:
    SUPPORTED={'UART0','UART1','FLASHCTL','I2C0','CPUSS','GPIOA','WWDT0','VREF',
               'TIMG0','TIMG1','TIMG2','TIMG4','SYSCTL','IOMUX','ADC0','ADC0_SVT'}
    BASES={'UART0':0x40108000,'UART1':0x40100000,'FLASHCTL':0x400cd000,
           'I2C0':0x400f0000,'GPIOA':0x400a0000,'WWDT0':0x40080000,'ADC0':0x40004000,
           'SYSCTL':0x400af000}
    # MSPM0L1306 datasheet Table 8-6; CPUSS IIDX encodes slot + 1.
    GROUPS={0:{'WWDT0':0,'FLASHCTL':3,'SYSCTL':6},1:{'GPIOA':0}}
    RESET_CAUSES={'sysresetreq':0x1b,'wwdt0':0x0e,'cpulockup':0x15,
                  'debug':0x1a,'por':3}
    RETAINED=tuple(range(0x400b0400,0x400b0410,4))

    def __init__(self,mcu):
        self.m=mcu; self.r=mcu.registers
        self.tx={0:bytearray(),1:bytearray()}; self.rx={0:deque(),1:deque()}
        self.gpio_inputs=0; self.adc_inputs={}; self.adc_pending=None; self.adc_stuck=False
        self.adc_sampling=False; self.adc_queue=deque(); self.adc_delay=32
        self.watchdog_deadline=None; self.watchdog_started=None; self.watchdog_feeds=0
        self.watchdog_tick_ratio=1000; self.watchdog_violations=[]
        self.writeonly_read_fixtures={}; self.irq_sources={}
        self.flash_delay=32;self.flash_deadline=None;self.flash_stuck=False
        self.flash=FlashControllerModel(lambda a,n:bytes(self.m.flash[a:a+n]),self.m.mutate_flash,busy=())
        self.flash.registers.update({a:v for a,v in self.r.items()
                                     if self.m.metadata[a].peripheral=='FLASHCTL'})
        self.r.update(self.flash.registers)
        self.expander=PowerIoPeripheral(bytes([0,0,0xff,0xff,0,0,0xff,0xff]),self.r)
        self.expander.mmio=self.r

    def _validate(self,address,size,writing=False):
        reg=self.m.metadata.get(address)
        if reg is None or size!=4 or address&3:
            raise BusFault(f'Invalid peripheral width/address {address:#x}/{size}')
        if reg.peripheral not in self.SUPPORTED:
            raise UnsupportedRegister(f'Unmodeled peripheral {reg.peripheral}.{reg.name}')
        if writing and reg.access=='read-only':raise BusFault(f'Write to read-only {reg.name}')
        if not writing and reg.access=='write-only' and address not in self.writeonly_read_fixtures:
            raise UnsupportedRegister(f'Unspecified write-only readback {reg.name}; supply explicit observed/test fixture')
        return reg

    def _trace(self,kind,address,value):
        self.m.trace.append((self.m.cycles,kind,address,value,self.m.cpu.reg_read(UC_ARM_REG_PC)))

    def reset_peripheral(self,name):
        for a,reg in self.m.metadata.items():
            if reg.peripheral==name:self.r[a]=reg.reset
        if name.startswith('UART'):self.rx[int(name[-1])].clear()
        if name=='WWDT0':self.watchdog_deadline=self.watchdog_started=None
        if name=='ADC0':
            self.adc_pending=None;self.adc_sampling=False;self.adc_queue.clear()
            for a,reg in self.m.metadata.items():
                if reg.peripheral=='ADC0_SVT':self.r[a]=reg.reset
        if name=='I2C0':
            self.expander.tx.clear();self.expander.rx.clear();self.expander.active=None
            self.expander.pending_irqs.clear()
        if name=='FLASHCTL':
            self.flash.pending=None;self.flash.polls.clear();self.flash_deadline=None
            self.flash.registers={a:self.r[a] for a,reg in self.m.metadata.items() if reg.peripheral==name}
        self._irq(name)

    def reset_system(self,reason='sysresetreq'):
        if reason not in self.RESET_CAUSES:
            raise ModelError(f'Unsupported peripheral reset domain/cause {reason!r}')
        retained={a:self.r[a] for a in self.RETAINED}
        previous=self.r[0x400b0220]&31
        self.irq_sources.clear()
        # SYSRST resets CPU/peripherals, not shutdown-store PMU retention.
        # POR here is an explicit virtual power-reset scenario, not boot-ROM emulation.
        for name in sorted(self.SUPPORTED):self.reset_peripheral(name)
        if reason!='por':self.r.update(retained)
        cause=self.RESET_CAUSES[reason]
        self.r[0x400b0220]=min(previous,cause) if previous else cause
        self.irq_sources.clear()
        for irq in set(IRQ.values()):self.m.set_irq_line(irq,False)

    def _irq(self,name):
        base=self.BASES.get(name)
        if base is None or name not in IRQ:return
        raw=self.r.get(base+0x1030,0);mask=self.r.get(base+0x1028,0)
        self.r[base+0x1038]=raw&mask
        self.irq_sources[name]=bool(raw&mask)
        irq=IRQ[name]
        self.m.set_irq_line(irq,any(active and IRQ[source]==irq for source,active in self.irq_sources.items()))
        for group,sources in self.GROUPS.items():
            if name in sources:
                bits=sum(1<<slot for source,slot in sources.items() if self.irq_sources.get(source,False))
                address=0x40401100+group*0x30
                self.r[address+0x10]=self.r[address+0x18]=bits

    def _uart_depth(self,port):
        return 4 if self.r[self.BASES['UART'+str(port)]+0x1100]&0x20000 else 1

    def _uart_rx_status(self,port):
        name='UART'+str(port);base=self.BASES[name]
        selection=(self.r[base+0x110c]>>4)&7
        threshold={0:1,1:1,2:2,3:3,4:4,5:4,6:2,7:1}[selection]
        if self._uart_depth(port)==1:threshold=1
        if len(self.rx[port])>=threshold:self.r[base+0x1030]|=1<<10
        else:self.r[base+0x1030]&=~(1<<10)
        self._irq(name)

    def inject_uart(self,port,data):
        base=self.BASES['UART'+str(port)]
        if not self.r[base+0x800]&1 or self.r[base+0x1100]&9!=9:
            self.m.events.append(('uart-rx-disabled',port,bytes(data)));return
        for value in data:
            if len(self.rx[port])>=self._uart_depth(port):
                self.r[base+0x1030]|=1<<4  # OE, not TXINT.
                continue
            self.rx[port].append(value)
        self._uart_rx_status(port)

    def set_gpio_inputs(self,value,mask=0xffffffff):
        old=self.gpio_inputs;self.gpio_inputs=((old&~mask)|(value&mask))&0xffffffff
        changed=(old^self.gpio_inputs)&~self.r[0x400a12c0]
        for pin in range(32):
            if changed&(1<<pin):
                selection=(self.r[0x400a1390+4*(pin//16)]>>(2*(pin%16)))&3
                edge=1 if self.gpio_inputs&(1<<pin) else 2
                if selection&edge:self.r[0x400a1030]|=1<<pin
        self._irq('GPIOA')

    def read(self,address,size=4):
        reg=self._validate(address,size);name=reg.peripheral;value=self.r[address]
        if reg.access=='write-only':
            value=self.writeonly_read_fixtures[address];self._trace('fixture-wo-read',address,value);return value
        base=self.BASES.get(name,0);offset=address-base
        if name=='FLASHCTL' and offset>=0x1100:
            if offset==0x13d0 and self.flash.pending is not None:value=4
            else:value=self.flash.read(address)
            self.r[address]=value
        elif name.startswith('UART'):
            port=int(name[-1])
            if offset==0x1108:
                value=0x40|(4 if not self.rx[port] else 0)|(8 if len(self.rx[port])>=self._uart_depth(port) else 0)
            elif offset==0x1124:
                if not self.rx[port]:raise MissingInput('Read from empty UART RX FIFO')
                value=self.rx[port].popleft();self._uart_rx_status(port)
        elif name=='WWDT0' and offset==0x1108:value=0  # Documented read-as-zero.
        elif name=='I2C0' and offset in (0x1218,0x121c,0x123c):value=self.expander.read(address)
        elif name=='GPIOA' and offset==0x1380:
            outputs=self.r.get(base+0x1280,0);enabled=self.r.get(base+0x12c0,0)
            value=(self.gpio_inputs&~enabled)|(outputs&enabled)
        elif address==0x400b0220:self.r[address]=0
        elif name=='CPUSS' and address in (0x40401100,0x40401130):
            bits=self.r[address+0x18];value=(bits&-bits).bit_length() if bits else 0
        if offset==0x1020 and name in self.BASES:
            bits=self.r.get(base+0x1030,0)&self.r.get(base+0x1028,0)
            value=(bits&-bits).bit_length() if bits else 0
            if bits:self.r[base+0x1030]&=~(bits&-bits)
            self._irq(name)
        if offset==0x1038 and name in self.BASES:
            value=self.r.get(base+0x1030,0)&self.r.get(base+0x1028,0)
        self._trace('read',address,value);return value

    def write(self,address,value,size=4):
        reg=self._validate(address,size,True);name=reg.peripheral
        value&=0xffffffff;self._trace('write',address,value)
        if reg.name.endswith('_RSTCTL'):
            if value>>24==0xb1:
                if value&1:self.reset_peripheral(name)
                status=address+0x10
                if status in self.r:
                    if value&1:self.r[status]|=0x10000
                    if value&2:self.r[status]&=~0x10000
            return
        if reg.name.endswith('_PWREN'):
            if value>>24==0x26:
                self.r[address]=value&1
                if name=='WWDT0' and not value&1:self.watchdog_deadline=self.watchdog_started=None
            return
        base=self.BASES.get(name,0);offset=address-base
        old=self.r[address];self.r[address]=value&reg.mask
        if name=='FLASHCTL' and offset>=0x1100:
            try:self.flash.write(address,value&reg.mask)
            except ValueError as error:raise ModelError(str(error)) from error
            if offset==0x1100 and value&1:
                self.flash_deadline=self.m.cycles+self.flash_delay
                self.r[base+0x13d0]=4
            return
        if name=='WWDT0':
            if offset in (0x1100,0x1104):
                key=0xc9 if offset==0x1100 else 0xbe
                if value>>24!=key:
                    self.r[address]=old;self._watchdog_violation('key');return
                if offset==0x1100 and self.watchdog_started is not None:
                    self.r[address]=old
                    raise UnsupportedRegister('WWDTCTL0 may only be initialized once before reset')
                if not self.r[base+0x800]&1:raise ModelError('WWDT configuration while peripheral disabled')
                self.r[address]=value&reg.mask&0xffffff
                if offset==0x1100:
                    self.watchdog_started=self.m.cycles
                    self.watchdog_deadline=self.m.cycles+self._watchdog_period()
                    self.r[base+0x110c]|=1
            elif offset==0x1108:
                self.r[address]=0
                if value!=0xa7:self._watchdog_violation('restart-key')
                else:self._feed_watchdog()
            # Interrupt mask/set/clear still use common path below.
        if name.startswith('UART'):
            if offset==0x1120:
                if not self.r.get(base+0x800,0)&1 or self.r.get(base+0x1100,0)&0x11!=0x11:
                    raise ModelError('UART TX while peripheral/module/transmitter disabled')
                self.tx[int(name[-1])].append(value&255)
            elif offset in (0x1100,0x110c):self._uart_rx_status(int(name[-1]))
        if name=='I2C0' and offset in (0x1220,0x1214,0x1238):
            self.r[0xe000e100]=self.m.enabled
            self.expander.write(address,value&reg.mask)
            # Hardware raw flags are independent of peripheral and NVIC masks.
            if offset==0x1214 and value&7==7 and self.expander.active and self.expander.active['nack']:
                self.r[base+0x1030]|=0x80
            self.expander.pending_irqs.clear();self._irq(name)
        if name=='GPIOA':
            operations={0x1290:(0x1280,'set'),0x12a0:(0x1280,'clear'),0x12b0:(0x1280,'toggle'),
                        0x12d0:(0x12c0,'set'),0x12e0:(0x12c0,'clear')}
            if offset in operations:
                target,op=operations[offset];current=self.r[base+target]
                self.r[base+target]={'set':current|value,'clear':current&~value,'toggle':current^value}[op]&0xffffffff
        if name in self.BASES:
            if offset==0x1040:self.r[base+0x1030]|=value&reg.mask
            elif offset==0x1048:self.r[base+0x1030]&=~(value&reg.mask)
            if offset in (0x1028,0x1040,0x1048):self._irq(name)
        if name=='ADC0' and offset==0x1104:
            if value&0x100 and not old&0x100:
                if not self.r[base+0x1100]&1:raise ModelError('ADC trigger without ENC')
                self._start_adc(value)
            elif old&0x100 and not value&0x100 and self.adc_sampling:
                self.adc_sampling=False;self.adc_pending=self.m.cycles+self.adc_delay
        if name=='SYSCTL' and offset==0x1304:
            self.r[address]=0
            if value>>24==0xe4 and value&1:
                level=self.r[base+0x1300]
                if level!=0:raise UnsupportedRegister('Boot/POR/BSL RESETCMD requires an explicit boot-domain model')
                self.m.request_reset('sysresetreq')

    def _start_adc(self,control):
        if self.adc_pending is not None or self.adc_sampling:raise ModelError('Overlapping ADC trigger')
        mode=(control>>16)&3;ctl2=self.r[0x40005108]
        if control&1 or mode>=2 or control&0x77000000 or ctl2&7:
            raise UnsupportedRegister('ADC model supports software single/sequence, unsigned 12-bit, no averaging')
        start=(ctl2>>16)&31;end=(ctl2>>24)&31 if mode==1 else start
        if not 0<=start<=end<4:raise UnsupportedRegister('ADC sequence outside the four physical MEMCTL registers')
        self.adc_queue=deque(range(start,end+1));self.r[0x40005340]|=1
        self.adc_sampling=bool(control&0x100000)
        if not self.adc_sampling:self.adc_pending=self.m.cycles+self.adc_delay

    def _watchdog_period(self):
        control=self.r[0x40081100]
        return (1<<[25,21,18,15,12,10,8,6][(control>>4)&7])*((control&7)+1)*self.watchdog_tick_ratio

    def _watchdog_violation(self,reason):
        self.watchdog_violations.append((self.m.cycles,reason))
        self.watchdog_deadline=None;self.r[0x4008110c]&=~1
        self.m.request_reset('wwdt0')

    def _feed_watchdog(self):
        if not self.r[0x40080800]&1:raise ModelError('WWDT restart while peripheral disabled')
        if self.watchdog_started is None:raise ModelError('WWDT restart before initialization')
        control=self.r[0x40081100];period=self._watchdog_period()
        if self.watchdog_started is not None and not control&0x10000:
            selection=(control>>(12 if self.r[0x40081104]&1 else 8))&7
            closed=period*[0,2,3,4,8,12,13,14][selection]//16
            if self.m.cycles-self.watchdog_started<closed:
                self._watchdog_violation('closed-window');return
        self.watchdog_feeds+=1;self.watchdog_started=self.m.cycles
        self.watchdog_deadline=self.m.cycles+period;self.r[0x4008110c]|=1

    def advance(self,now):
        if self.flash_deadline is not None and now>=self.flash_deadline and not self.flash_stuck:
            self.r[0x400ce3d0]=self.flash.read(0x400ce3d0)
            self.flash_deadline=None;self.r[0x400ce030]|=1;self._irq('FLASHCTL')
        if self.watchdog_deadline is not None and self.m.sleeping and self.r[0x40081100]&0x20000:
            raise UnsupportedRegister('WWDT sleep gating requires explicit POLICY/clock-domain support')
        if self.watchdog_deadline is not None and now>=self.watchdog_deadline:
            if self.r[0x40081100]&0x10000:
                self.r[0x40081030]|=1;self._irq('WWDT0')
                period=self._watchdog_period()
                self.watchdog_deadline+=((now-self.watchdog_deadline)//period+1)*period
            else:self._watchdog_violation('expired')
        while self.adc_pending is not None and now>=self.adc_pending and not self.adc_stuck:
            i=self.adc_queue[0];channel=self.r[0x40005180+4*i]&31
            if channel not in self.adc_inputs:raise MissingInput(f'ADC channel {channel} has no explicit input sample')
            value=self.adc_inputs[channel]
            if not 0<=value<=0xfff:raise ModelError('ADC input must be an explicit unsigned 12-bit sample')
            self.r[0x40005280+4*i]=self.r[0x4055a280+4*i]=value
            self.r[0x40005030]|=1<<(8+i);self._irq('ADC0');self.adc_queue.popleft()
            if self.adc_queue and self.r[0x40005100]&1:self.adc_pending+=self.adc_delay
            else:
                self.adc_queue.clear();self.adc_pending=None
                self.r[0x40005104]&=~0x100;self.r[0x40005340]&=~1
