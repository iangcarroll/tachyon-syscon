"""Physical address-space and exception model; no fabricated executable stubs.

Instruction quanta advance a deterministic virtual clock, NOT silicon cycles.
Peripheral clock events can also be advanced explicitly for reproducible tests.
"""
import collections
import struct
from unicorn import *
from unicorn.arm_const import *
from .profile import PROFILE,registers

class ModelError(RuntimeError):pass
class BusFault(ModelError):pass
class MissingImage(ModelError):pass
class UnsupportedRegister(ModelError):pass
class Lockup(ModelError):pass

class MCU:
    def __init__(self,image,*,factory=None,nonmain=None,sram=None,peripherals=True,fault_policy="stop"):
        if fault_policy not in ('stop','hardfault'):raise ValueError('fault_policy must be stop or hardfault')
        self.fault_policy=fault_policy;self._running=False;self.locked_up=False;self.irq_lines=0
        if len(image)>65536:raise ValueError('Image exceeds physical flash')
        if factory is not None and len(factory)!=128:raise ValueError('Factory image must be128 bytes')
        if nonmain is not None and len(nonmain)!=512:raise ValueError('NONMAIN image must be512 bytes')
        if sram is not None and len(sram)!=4096:raise ValueError('SRAM image must be4096 bytes')
        self.profile=PROFILE.copy();self.cpu=Uc(UC_ARCH_ARM,UC_MODE_THUMB|UC_MODE_MCLASS)
        self.cpu.ctl_set_cpu_model(UC_CPU_ARM_CORTEX_M0)
        self.flash=bytearray(image)+bytearray(b'\xff'*(65536-len(image)))
        self.factory=factory;self.nonmain=nonmain
        self.metadata=registers();self.registers={a:r.reset for a,r in self.metadata.items()}
        self.trace=collections.deque(maxlen=20000);self.executed=set();self.visits=collections.Counter()
        self.cycles=0;self.instructions=0;self.events=[];self.stop_reason=None
        self.enabled=0;self.pending=set();self.active=[];self.priorities=[0]*48
        self.vtor=0;self.systick_ctrl=0;self.systick_load=0;self.systick_current=0;self.countflag=False
        self.sleeping=False;self._transition=None;self.breakpoints=set();self.reset_count=0
        self._map(0,65536,UC_PROT_READ|UC_PROT_EXEC,self.flash)
        self._map(0x400000,65536,UC_PROT_READ|UC_PROT_EXEC,self.flash)
        self._map(0x20000000,4096,UC_PROT_ALL,sram or bytes(4096))
        for base,data in ((0x41c00000,nonmain),(0x41c10000,nonmain),(0x41c40000,factory),(0x41c50000,factory)):
            self._map(base,4096,UC_PROT_READ,data or b'')
        for page in sorted({a&~4095 for a in self.metadata}|{0xe000e000}):self._map(page,4096,UC_PROT_READ|UC_PROT_WRITE)
        self.cpu.hook_add(UC_HOOK_CODE,self._code)
        self.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self._memory)
        self.cpu.hook_add(UC_HOOK_MEM_INVALID,self._invalid)
        self.cpu.hook_add(UC_HOOK_INTR,self._interrupt)
        self.device=None
        if peripherals:
            from .peripherals import Devices
            self.device=Devices(self)
        self.reset_cpu()

    def _map(self,address,size,permissions,data=b''):
        self.cpu.mem_map(address,size,permissions)
        if data:self.cpu.mem_write(address,bytes(data))

    def _read_special(self,register):
        # Unicorn's public M-class special-register API applies MRS privilege
        # checks. Exception hardware must inspect the underlying bank even
        # while Thread mode is unprivileged. No guest instruction executes in
        # this temporary privileged register-access context.
        psr=self.cpu.reg_read(UC_ARM_REG_XPSR)
        unprivileged=not psr&63 and self.cpu.reg_read(UC_ARM_REG_CONTROL)&1
        if unprivileged:self.cpu.reg_write(UC_ARM_REG_XPSR,psr|3)
        try:return self.cpu.reg_read(register)
        finally:
            if unprivileged:self.cpu.reg_write(UC_ARM_REG_XPSR,psr)

    def _write_special(self,register,value):
        psr=self.cpu.reg_read(UC_ARM_REG_XPSR)
        unprivileged=not psr&63 and self.cpu.reg_read(UC_ARM_REG_CONTROL)&1
        if unprivileged:self.cpu.reg_write(UC_ARM_REG_XPSR,psr|3)
        try:self.cpu.reg_write(register,value)
        finally:
            if unprivileged:self.cpu.reg_write(UC_ARM_REG_XPSR,psr)

    def reset_cpu(self):
        sp,pc=struct.unpack_from('<II',self.flash);sp&=~3
        if not 0x20000000<sp<=0x20001000 or not pc&1:raise BusFault('Invalid initial vector/SP')
        for reg in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,
                    UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12):
            self.cpu.reg_write(reg,0)
        self._write_special(UC_ARM_REG_CONTROL,0);self.cpu.reg_write(UC_ARM_REG_PRIMASK,0)
        self.cpu.reg_write(UC_ARM_REG_XPSR,1<<24);self.cpu.reg_write(UC_ARM_REG_MSP,sp)
        self.cpu.reg_write(UC_ARM_REG_PSP,0)
        self.cpu.reg_write(UC_ARM_REG_LR,0xffffffff);self.cpu.reg_write(UC_ARM_REG_PC,pc)
        self.enabled=0;self.pending.clear();self.active.clear();self.vtor=0;self.priorities=[0]*48
        self.irq_lines=0;self.locked_up=False
        self.registers.pop(0xe000ed10,None);self.registers.pop(0xe000ed14,None)
        self.systick_ctrl=4;self.systick_load=self.systick_current=0;self.countflag=False
        self.sleeping=False;self._transition=None;self.stop_reason=None

    def request_reset(self,cause='sysresetreq'):
        self._transition=('reset',cause)
        if self._running:self.cpu.emu_stop()

    def reset_system(self,reason='sysresetreq'):
        # Reset domains beyond the CPU belong to the TI device model.
        self.reset_cpu()
        if self.device:self.device.reset_system(reason)
        self.reset_count+=1
        self.events.append(('system-reset',reason,self.cycles))

    def set_irq_line(self,irq_number,asserted):
        if not 0<=irq_number<32:raise ValueError(irq_number)
        bit=1<<irq_number
        if asserted:
            if not self.irq_lines&bit:self.pend(irq_number+16)
            self.irq_lines|=bit
        else:self.irq_lines&=~bit

    def _lockup(self,message):
        self.locked_up=True;self.sleeping=False
        self.cpu.reg_write(UC_ARM_REG_PC,0xfffffffe)
        self.events.append(('lockup',message,self.cycles))
        raise Lockup(message)

    def _fault(self,error):
        if self.fault_policy=='stop':raise error
        if self.active and self._priority(self.active[-1])<=-1:
            self._lockup(f'Fault at NMI/HardFault priority: {error}')
        self.events.append(('hardfault',str(error),self.cpu.reg_read(UC_ARM_REG_PC),self.cycles))
        try:self.enter_exception(3)
        except (BusFault,MissingImage) as stack_error:
            self._lockup(f'HardFault entry failed: {stack_error}')

    def _flash_address(self,address):
        if 0<=address<65536:return address
        if 0x400000<=address<0x410000:return address-0x400000
        return None

    def check_memory(self,address,size,kind):
        if address<0 or size<=0 or address+size>0x100000000:raise BusFault('Wrapped memory transaction')
        offset=self._flash_address(address)
        if offset is not None:
            if kind=='write':raise BusFault(f'CPU flash store at{address:#x}')
            if offset+size>65528:raise BusFault(f'Flash prefetch exclusion at{address:#x}')
            return
        if 0x20000000<=address and address+size<=0x20001000:return
        for base,length,payload in ((0x41c00000,512,self.nonmain),(0x41c10000,512,self.nonmain),
                                    (0x41c40000,128,self.factory),(0x41c50000,128,self.factory)):
            if base<=address<base+4096:
                if address+size>base+length or kind!='read':raise BusFault(f'{kind} outside readonly region at{address:#x}')
                if payload is None:raise MissingImage(f'No captured/fixture contents supplied for{base:#x}')
                return
        if 0xe000e000<=address<0xe000f000 and kind!='execute':return
        if address in self.metadata and size==4 and kind!='execute':return
        raise BusFault(f'{kind} outside implemented address space at{address:#x} size{size}')

    def read(self,address,size):
        self.check_memory(address,size,'read')
        if address in self.metadata or 0xe000e000<=address<0xe000f000:return self.read_register(address,size).to_bytes(size,'little')
        return bytes(self.cpu.mem_read(address,size))

    def write_ram(self,address,data):
        if not 0x20000000<=address or address+len(data)>0x20001000:raise BusFault('Host RAM fixture exceedsphysicalSRAM')
        self.cpu.mem_write(address,bytes(data))

    def mutate_flash(self,address,data):
        # Exclusive controller/environment path, not exposed as a CPU writable mapping.
        if address<0 or address+len(data)>65536:raise BusFault('Controller mutation outside flash')
        self.flash[address:address+len(data)]=data
        for base in (0,0x400000):self.cpu.mem_write(base+address,bytes(data))
        self.cpu.ctl_remove_cache(address,address+len(data))
        self.cpu.ctl_remove_cache(0x400000+address,0x400000+address+len(data))

    def _memory(self,uc,access,address,size,value,_):
        kind='write' if access==UC_MEM_WRITE else 'read'
        if size in (2,4,8) and address%size:raise BusFault(f'Unaligned CPU {kind} at {address:#x}/{size}')
        self.check_memory(address,size,kind)
        if address in self.metadata or 0xe000e000<=address<0xe000f000:
            if kind=='write':self.write_register(address,value,size)
            else:uc.mem_write(address,self.read_register(address,size).to_bytes(size,'little'))

    def _invalid(self,uc,access,address,size,value,_):
        self._bus_fault=BusFault(f'Unmapped/protected access type {access} at {address:#x} size {size} PC {uc.reg_read(UC_ARM_REG_PC):#x}')
        return False

    def pend(self,exception):
        if exception not in (2,3,11,14,15) and not 16<=exception<48:raise ValueError(exception)
        self.pending.add(exception)

    def _priority(self,exception):return -2 if exception==2 else -1 if exception==3 else self.priorities[exception]

    def _next_exception(self,ignore_primask=False,ignore_active=False):
        candidates=[n for n in self.pending if n<16 or self.enabled&(1<<(n-16))]
        if not ignore_primask and self._read_special(UC_ARM_REG_PRIMASK):candidates=[n for n in candidates if n in (2,3)]
        if self.active and not ignore_active:candidates=[n for n in candidates if self._priority(n)<self._priority(self.active[-1])]
        return min(candidates,key=lambda n:(self._priority(n),n)) if candidates else None

    def enter_exception(self,number):
        uc=self.cpu;oldpsr=uc.reg_read(UC_ARM_REG_XPSR);control=uc.reg_read(UC_ARM_REG_CONTROL)
        use_psp=not self.active and bool(control&2)
        bank=UC_ARM_REG_PSP if use_psp else UC_ARM_REG_MSP
        sp=self._read_special(bank);alignment=bool(sp&4);newsp=(sp-32)&~7
        regs=(UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12,UC_ARM_REG_LR,UC_ARM_REG_PC)
        values=[uc.reg_read(r) for r in regs]+[(oldpsr&~(1<<9))|(int(alignment)<<9)]
        self._write_special(bank,newsp);self.write_ram(newsp,struct.pack('<8I',*values))
        original_number=number
        try:handler=int.from_bytes(self.read(self.vtor+number*4,4),'little')
        except BusFault as error:
            if number in (2,3):self._lockup(f'Fault reading vector {number}: {error}')
            if self.fault_policy=='stop':raise
            if self.active and self._priority(self.active[-1])<=-1:self._lockup('Vector fault at fixed priority')
            number=3
            self.events.append(('derived-hardfault',original_number,str(error),self.cycles))
            try:handler=int.from_bytes(self.read(self.vtor+12,4),'little')
            except BusFault as nested:self._lockup(f'HardFault vector read failed: {nested}')
        invalid_thumb=not handler&1
        uc.reg_write(UC_ARM_REG_LR,0xfffffff1 if self.active else 0xfffffffd if use_psp else 0xfffffff9)
        uc.reg_write(UC_ARM_REG_XPSR,(oldpsr&0xf0000000)|(1<<24)|number)
        uc.reg_write(UC_ARM_REG_CONTROL,control&~2)
        uc.reg_write(UC_ARM_REG_PC,handler)
        self.pending.discard(number);self.active.append(number);self.sleeping=False
        self.events.append(('exception-enter',number,newsp,self.cycles))
        if invalid_thumb:
            if number in (2,3):self._lockup(f'Invalid NMI/HardFault vector {number}: {handler:#x}')
            raise BusFault(f'Invalid exception vector {number}: {handler:#x}')

    def return_exception(self,token):
        if not self.active or token not in (0xfffffff1,0xfffffff9,0xfffffffd):
            self._lockup('Invalid EXC_RETURN')
        thread=bool(token&8)
        if thread!=(len(self.active)==1):self._lockup('EXC_RETURN nesting mismatch')
        if self.cpu.reg_read(UC_ARM_REG_XPSR)&63!=self.active[-1]:
            self._lockup('Returning exception not active in IPSR')
        bank=UC_ARM_REG_PSP if token&4 else UC_ARM_REG_MSP;sp=self.cpu.reg_read(bank)
        values=struct.unpack('<8I',self.read(sp,32));psr=values[-1]
        control=self.cpu.reg_read(UC_ARM_REG_CONTROL)
        ipsr=0 if thread and control&1 else psr&63
        if (thread and ipsr) or (not thread and ipsr!=self.active[-2]):
            self._lockup('Stacked IPSR inconsistent with return mode')
        if values[6]&1:self._lockup('Unpredictable odd stacked return PC')
        regs=(UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R12,UC_ARM_REG_LR)
        for reg,value in zip(regs,values):self.cpu.reg_write(reg,value)
        self.cpu.reg_write(bank,(sp+32)|(4 if psr&(1<<9) else 0))
        self.cpu.reg_write(UC_ARM_REG_CONTROL,(control&~2)|(2 if token&4 else 0))
        self.cpu.reg_write(UC_ARM_REG_PC,values[6]|1)
        self.cpu.reg_write(UC_ARM_REG_XPSR,(psr&0xf1000000)|ipsr)
        number=self.active.pop();self.events.append(('exception-return',number,self.cycles))
        if number>=16 and self.irq_lines&(1<<(number-16)):self.pend(number)
        if not psr&(1<<24):raise BusFault('Exception frame lost Thumb bit')
        if thread and self.registers.get(0xe000ed10,0)&2:self.sleeping=True

    def _interrupt(self,uc,number,_):
        if number==8 and uc.reg_read(UC_ARM_REG_PC)>=0xfffffff0:
            if not self.active:raise BusFault('Exception return address executed in Thread mode')
            self._transition=('return',uc.reg_read(UC_ARM_REG_PC)|1);uc.emu_stop();return
        if number==2:
            # SVC is synchronous: it cannot remain pending behind PRIMASK or
            # a handler of equal/higher priority. Such cases escalate.
            if self._read_special(UC_ARM_REG_PRIMASK) or (self.active and self._priority(11)>=self._priority(self.active[-1])):
                raise BusFault('SVCall priority escalation')
            self.pend(11);self._transition=('exception',11);uc.emu_stop();return
        if number in (1,3,4,7):raise BusFault(f'CPU abort{number} at{uc.reg_read(UC_ARM_REG_PC):#x}')
        raise ModelError(f'Unmodeled CPU exception{number} at{uc.reg_read(UC_ARM_REG_PC):#x}')

    def _validate_instruction(self,address,size,opcode):
        # Unicorn accepts some ARMv7-M encodings even for its Cortex-M0 CPU.
        # ARMv6-M 32-bit instructions are BL, MRS/MSR, and DSB/DMB/ISB.
        if size==4:
            second=int.from_bytes(self.cpu.mem_read(address+2,2),'little')
            branch=(opcode&0xf800)==0xf000 and (second&0xd000)==0xd000
            special={0,1,2,3,5,6,7,8,9,16,20}
            mrs=opcode==0xf3ef and second&0xf000==0x8000 and second&255 in special and (second>>8)&15 not in (13,15)
            msr=opcode&0xfff0==0xf380 and second&0xff00==0x8800 and second&255 in {0,1,2,3,8,9,16,20} and opcode&15 not in (13,15)
            barrier=opcode==0xf3bf and second in (0x8f4f,0x8f5f,0x8f6f)
            if not (branch or mrs or msr or barrier):
                raise BusFault(f'Instruction outside ARMv6-M at {address:#x}: {opcode:04x} {second:04x}')
        elif (opcode&0xff00==0xbf00 and opcode&15) or opcode&0xf500==0xb100:
            raise BusFault(f'ARMv7-only IT/CBZ instruction at {address:#x}: {opcode:04x}')

    def _code(self,uc,address,size,_):
        self.check_memory(address,size,'execute')
        if address in self.breakpoints:self.stop_reason=('breakpoint',address);uc.emu_stop();return
        number=self._next_exception()
        if number is not None:self._transition=('exception',number);uc.emu_stop();return
        opcode=int.from_bytes(uc.mem_read(address,2),'little')
        self.executed.add(address);self.visits[address]+=1;self.instructions+=1;self.advance(1)
        if self._transition:return
        self._validate_instruction(address,size,opcode)
        if opcode in (0xbf20,0xbf40):raise ModelError('WFE/SEV event-register behavior is not implemented')
        if self.active and opcode==0x4770 and uc.reg_read(UC_ARM_REG_LR)>=0xfffffff0:
            self._transition=('return',uc.reg_read(UC_ARM_REG_LR));uc.emu_stop();return
        if opcode==0xbf30:
            uc.reg_write(UC_ARM_REG_PC,address+2|1)
            self.sleeping=self._next_exception(ignore_primask=True) is None
            if self.sleeping:self.stop_reason=('wfi',address)
            uc.emu_stop()

    def advance(self,ticks):
        if not isinstance(ticks,int) or ticks<0:raise ValueError('ticks must be a nonnegative integer')
        self.cycles+=ticks
        if self.systick_ctrl&1:
            while ticks:
                if self.systick_current==0:
                    if not self.systick_load:break
                    self.systick_current=self.systick_load;ticks-=1
                    if not ticks:break
                consumed=min(ticks,self.systick_current);ticks-=consumed;self.systick_current-=consumed
                if self.systick_current==0:
                    self.countflag=True
                    if self.systick_ctrl&2:self.pend(15)
        if self.device:self.device.advance(self.cycles)

    def run(self,instructions=100000,until=None):
        if instructions<0:raise ValueError('Negative instruction budget')
        if self.locked_up:raise Lockup('CPU is locked up; reset is required')
        self.stop_reason=None;start=self.instructions;limit=start+instructions
        if until is not None:self.breakpoints.add(until)
        self._running=True
        try:
            while self.instructions<limit:
                if self._transition and self._transition[0]=='reset':
                    self.reset_system(self._transition[1]);continue
                if self.sleeping:
                    if self._next_exception(ignore_primask=True) is None:
                        self.stop_reason=('wfi',self.cpu.reg_read(UC_ARM_REG_PC));break
                    self.sleeping=False
                self._transition=None;self._bus_fault=None
                try:
                    self.cpu.emu_start(self.cpu.reg_read(UC_ARM_REG_PC)|1,0xffffffff,count=limit-self.instructions)
                    if self._transition:
                        kind,value=self._transition
                        if kind=='exception':self.enter_exception(value)
                        elif kind=='return':self.return_exception(value)
                        elif kind=='reset':self.reset_system(value)
                        continue
                except BusFault as error:
                    self._fault(error);continue
                except UcError as error:
                    if error.errno==UC_ERR_INSN_INVALID:
                        fault=BusFault(f'Undefined ARMv6-M instruction at {self.cpu.reg_read(UC_ARM_REG_PC):#x}')
                    elif error.errno in (UC_ERR_READ_UNMAPPED,UC_ERR_WRITE_UNMAPPED,UC_ERR_FETCH_UNMAPPED,UC_ERR_READ_PROT,UC_ERR_WRITE_PROT,UC_ERR_FETCH_PROT):
                        fault=self._bus_fault or BusFault(f'CPU memory access failed: {error}')
                    else:raise
                    self._fault(fault)
                    continue
                if self.stop_reason:break
                if self.instructions==start:raise ModelError('CPU stopped without progress')
            if not self.stop_reason:self.stop_reason=('instruction-budget',self.instructions-start)
            return self.stop_reason
        finally:
            self._running=False
            if until is not None:self.breakpoints.discard(until)

    def read_register(self,address,size=4):
        if 0xe000e000<=address<0xe000f000:return self._ppb(address,None,size)
        if self.device:return self.device.read(address,size)
        raise UnsupportedRegister(f'No peripheral model for{address:#x}')

    def write_register(self,address,value,size=4):
        if 0xe000e000<=address<0xe000f000:return self._ppb(address,value,size)
        if self.device:return self.device.write(address,value,size)
        raise UnsupportedRegister(f'No peripheral model for{address:#x}')

    def _ppb(self,a,value,size):
        writing=value is not None
        if size not in (1,2,4) or a%size:raise BusFault('PPB width/alignment')
        if not self.active and self.cpu.reg_read(UC_ARM_REG_CONTROL)&1:raise BusFault('UnprivilegedPPBaccess')
        if not (0xe000e400<=a<a+size<=0xe000e420 or 0xe000ed1c<=a<a+size<=0xe000ed24) and size!=4:
            raise BusFault('PPB register requires word access')
        if a==0xe000ed00 and not writing:return 0x410cc601
        if a==0xe000ed08:
            if writing:self.vtor=value&0xffffff00
            return self.vtor
        if a==0xe000e010:
            if writing:self.systick_ctrl=(value&3)|4
            result=self.systick_ctrl|(int(self.countflag)<<16)
            if not writing:self.countflag=False
            return result
        if a==0xe000e014:
            if writing:self.systick_load=value&0xffffff
            return self.systick_load
        if a==0xe000e018:
            if writing:self.systick_current=0;self.countflag=False
            return self.systick_current
        if a==0xe000e01c and not writing:return 1<<31
        if a in (0xe000e100,0xe000e180):
            if writing:self.enabled=(self.enabled|value) if a==0xe000e100 else self.enabled&~value
            return self.enabled
        if a in (0xe000e200,0xe000e280):
            if writing:
                for i in range(32):
                    if value&(1<<i):
                        if a==0xe000e200:self.pend(i+16)
                        elif not self.irq_lines&(1<<i):self.pending.discard(i+16)
            return sum(1<<(n-16) for n in self.pending if n>=16)
        if a==0xe000e300 and not writing:return sum(1<<(n-16) for n in self.active if n>=16)
        if 0xe000e400<=a<a+size<=0xe000e420:
            index=a-0xe000e400+16
            if writing:
                for i in range(size):self.priorities[index+i]=(value>>(8*i))&0xc0
            return sum(self.priorities[index+i]<<(8*i) for i in range(size))
        if 0xe000ed1c<=a<a+size<=0xe000ed24:
            numbers=[0,0,0,11,0,0,14,15];offset=a-0xe000ed1c
            if writing:
                for i in range(size):
                    n=numbers[offset+i]
                    if n:self.priorities[n]=(value>>(i*8))&0xc0
            return sum((self.priorities[numbers[offset+i]] if numbers[offset+i] else 0)<<(i*8) for i in range(size))
        if a==0xe000ed04:
            if writing:
                if value&(1<<28):self.pend(14)
                if value&(1<<27):self.pending.discard(14)
                if value&(1<<26):self.pend(15)
                if value&(1<<25):self.pending.discard(15)
                if value&(1<<31):self.pend(2)
            return (self.active[-1] if self.active else 0)|((self._next_exception(ignore_primask=True,ignore_active=True) or 0)<<12)|(int(any(n>=16 for n in self.pending))<<22)|(int(14 in self.pending)<<28)|(int(15 in self.pending)<<26)|(int(2 in self.pending)<<31)
        if a==0xe000ed0c:
            if writing and value>>16==0x5fa and value&4:self.request_reset('sysresetreq')
            return 0xfa050000
        if a==0xe000ed10:
            if writing:self.registers[a]=value&0x16
            return self.registers.get(a,0)
        if a==0xe000ed14:return 0x208
        raise UnsupportedRegister(f'Unknown PPBregister{a:#x}')
