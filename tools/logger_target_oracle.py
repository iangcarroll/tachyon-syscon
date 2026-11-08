"""Source-backed ARM logger frames, with explicit UART/time/color test ports."""
from pathlib import Path
import struct
from unicorn import UC_HOOK_MEM_INVALID,UC_HOOK_CODE,UcError
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
from oracle import Oracle
from arm_rebuild_oracle import ArmRebuildOracle
import build_runtime_scan_image as runtime
REGS=[UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11,UC_ARM_REG_R12]
def build(destination,real_uart=False):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    traps=destination/'logger_ports.S'
    ports=['syscon_target_now','syscon_target_color'] if real_uart else ['syscon_target_uart_write','syscon_target_now','syscon_target_color']
    traps.write_text('.syntax unified\n.thumb\n'+''.join(f'.global {n}\n.type {n},%function\n.thumb_func\n{n}:\n bkpt #0\n bx lr\n' for n in ports))
    old=runtime.SOURCES
    try:
        runtime.SOURCES=old+['src/format.c','target/logger_target.c','target/logger_state.c','target/logger_target_abi.S',str(traps)]
        if real_uart:runtime.SOURCES+=['target/uart_ring.c','target/uart_state.c','target/uart_ring_abi.S','target/hal_helpers.c','target/logger_uart_test_fixture.c']
        return runtime.build(destination)
    finally:runtime.SOURCES=old

class LoggerPair:
    SP=0x20000f00
    owners=None
    def __init__(self,elf,colors=(0,0),now=123,real_uart=False):
        if self.owners is not None:self.owners.append(self)
        self.cpus=[Oracle(),ArmRebuildOracle(elf)]
        self.cpus[0].cpu.mem_map(0x010ff000,4096)
        self.events=[[],[]];self.faults=[[],[]];self.colors=[list(colors),list(colors)];self.now=now;self.after_write=None
        self.frames=[None,None]
        for index,cpu in enumerate(self.cpus):
            entry=0x8e8c if index==0 else cpu.symbols['syscon_logger_target_vlog']&~1
            def enter(uc,address,size,user,index=index,entry=entry):
                if address==entry:
                    self.frames[index]=(uc.reg_read(UC_ARM_REG_SP)-368,uc.reg_read(UC_ARM_REG_LR))
            cpu.cpu.hook_add(UC_HOOK_CODE,enter)
            def invalid(uc,access,address,size,value,user,index=index):
                self.faults[index].append((access,address,size,value));return False
            cpu.cpu.hook_add(UC_HOOK_MEM_INVALID,invalid)
            def color(o,index=index):
                value=self.colors[index].pop(0);self.events[index].append(('color',value));return value
            def clock(o,index=index):
                self.events[index].append(('time',self.now))
                o.cpu.reg_write(UC_ARM_REG_R1,self.now>>32)
                return self.now if index else self.now&0xffffffff
            def write(o,index=index):
                port,address,size=(0,o.arg(0),o.arg(1)) if index==0 else (o.arg(0),o.arg(1),o.arg(2))
                self.capture(index,port,address,size)
            def sg_write(o,index=index):self.capture(index,o.arg(0),o.arg(1),o.arg(2))
            addresses=[0x312c,0x77b4,0x3af4,0x8c8c] if index==0 else [cpu.symbols[n]&~1 for n in ['syscon_target_color','syscon_target_now','syscon_target_uart_write']]
            for address,callback in zip(addresses,[color,clock,write,sg_write]):
                if not (real_uart and index==1 and callback is write):cpu.hooks[address]=callback
        if real_uart:
            from unicorn import UC_HOOK_MEM_WRITE
            for index,cpu in enumerate(self.cpus):
                for base in (0x40108000,0x40100000,0x400b0000):cpu.cpu.mem_map(base,0x2000)
                if index==0:
                    cpu.hooks.pop(0x3af4);cpu.hooks.pop(0x8c8c)
                def tx(uc,access,address,size,value,user,index=index):
                    if address in (0x40109120,0x40101120,0x400b040c):self.events[index].append(('mmio',address,size,value))
                cpu.cpu.hook_add(UC_HOOK_MEM_WRITE,tx)
        self.put(0x2000080c,b'\1')
        self.put(0x20000a00,bytes((i*73+29)&255 for i in range(0x600)))
    def put(self,address,data):
        for cpu in self.cpus:cpu.put(address,data)
    def capture(self,index,port,address,size):
        data=bytearray()
        for offset in range(size):
            try:data+=self.cpus[index].cpu.mem_read((address+offset)&0xffffffff,1)
            except UcError:
                self.events[index].append(('uart-fault',port,address,size,bytes(data),(address+offset)&0xffffffff))
                raise
        self.events[index].append(('write',port,address,size,bytes(data)))
        if self.after_write:self.after_write(self,index,port,address,size)
    def normalized_events(self,index):
        """Compare bytes/order while allowing linked constants and return PCs.

        The original's overlong-prefix bug can expose its saved LR. Check that
        word against the actual observed call return before normalizing it;
        a stale original-address literal must fail, not be hidden by a mask.
        """
        result=[]
        for event in self.events[index]:
            if event[0] not in ('write','uart-fault'):
                result.append(event);continue
            kind,port,address,size,data,*fault=event
            frame=self.frames[index]
            if frame and address==frame[0]+24 and len(data)>=344:
                saved=data[340:344]
                assert saved==struct.pack('<I',frame[1]),'Saved return does not match linked call'
                data=data[:340]+b'RETN'+data[344:]
            # A UART write's constant source address is private implementation
            # data; contents, port, size and all fault addresses remain exact.
            source='constant' if address<0x10000 or 0x01000000<=address<0x01080000 else address
            result.append((kind,port,source,size,data,*fault))
        return result
    def call(self,address,symbol,*args,compare_result=False):
        results=[]
        for index,cpu in enumerate(self.cpus):
            for n,reg in enumerate(REGS):cpu.cpu.reg_write(reg,0x5a000000+n*0x10101)
            cpu.cpu.reg_write(UC_ARM_REG_SP,self.SP)
            cpu.cpu.reg_write(UC_ARM_REG_LR,0x010fff01)
            for i,arg in enumerate(args):
                if i<4:cpu.cpu.reg_write(REGS[i],arg&0xffffffff)
                else:cpu.put(self.SP+4*(i-4),struct.pack('<I',arg&0xffffffff))
            try:
                cpu.cpu.emu_start((address if index==0 else cpu.symbols[symbol])|1,0x010fff00,count=1000000)
                assert cpu.cpu.reg_read(UC_ARM_REG_PC)==0x010fff00
                results.append(('return',cpu.cpu.reg_read(UC_ARM_REG_R0)))
            except UcError as e:results.append(('fault',e.errno))
        assert self.normalized_events(0)==self.normalized_events(1),self.events
        assert results[0][0]==results[1][0],results
        assert self.faults[0]==self.faults[1],self.faults
        if results[0][0]=='return':
            assert [self.cpus[0].cpu.reg_read(r) for r in REGS[4:12]]==[self.cpus[1].cpu.reg_read(r) for r in REGS[4:12]]
            assert self.cpus[0].cpu.reg_read(UC_ARM_REG_SP)==self.cpus[1].cpu.reg_read(UC_ARM_REG_SP)
        if compare_result:assert results[0]==results[1]
        return results
