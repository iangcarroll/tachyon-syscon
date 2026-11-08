"""Recompiled command/parser/runtime; external hardware endpoints explicit.

Printer/logger callbacks execute real ARM variadic fixture code on both sides.
No scan/string/command/parser implementation is replaced by a Python model.
"""
import hashlib,json,struct,re
from pathlib import Path
from elftools.elf.elffile import ELFFile
from unicorn import UC_HOOK_MEM_WRITE,UC_PROT_READ,UC_PROT_EXEC
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_LR,UC_ARM_REG_R0,UC_ARM_REG_R1
from ioexpander_target_oracle import CALLEE
import build_runtime_scan_image as runtime
from arm_rebuild_oracle import ArmRebuildOracle
from oracle import Oracle,REPLACED_ENDPOINTS
from power_state_comparison import text_argument
ROOT=Path(__file__).resolve().parents[1]
ALL_COMMANDS={int(a,16):n for a,n in json.loads((ROOT/'analysis/command-target-symbols.json').read_text()).items()}
OWNED=[0x3ef0,0x3f24,0x3f80,0x3fd0,0x40a0,0x40fc,0x4110,0x41a4,0x422c,0x4258,0x42c8,0x4320,0x4364,0x4420,0x47b0,0x47bc,0x47fc,0x4850,0x48a4,0x48e0,0x4904,0x4970,0x49ac]
MAPPINGS={a:ALL_COMMANDS[a] for a in OWNED}
DEPENDENCIES={0x39e8:('syscon_target_ioexpander_read',2),0x80f8:('syscon_target_gpio_read',1),
    0x5358:('syscon_target_power_report',1),0x6650:('syscon_target_modem_wake_remaining',0),
    0x65f0:('syscon_target_modem_wake_schedule',1),0x74f8:('syscon_mcu_sleep',0),
    0x37e4:('syscon_target_ioexpander_reset',0),0x5a88:('syscon_target_retained_clear_registers',0),
    0x77c0:('syscon_target_timer_delay',1),0x55dc:('syscon_target_shutdown_set',1),
    0x74e8:('syscon_target_modem_raw_send',2),0x6428:('syscon_target_modem_poweron',0),
    0x65e4:('syscon_target_modem_fastboot',0),0x65d0:('syscon_target_modem_fct',0),
    0x64a0:('syscon_target_modem_edl',0),0x5dc8:('syscon_target_rgb_get_config',1),
    0x5df4:('syscon_target_rgb_state_name',1),0x5e0c:('syscon_target_rgb_pattern_name',1),
    0x5c68:('syscon_target_rgb_preset',2),0x5c38:('syscon_target_rgb_configure',1),
    0x4c50:('syscon_target_power_measure',1),0x5274:('syscon_target_power_battery_detect',0),
    0x7468:('syscon_target_modem_key_pulse',2),0x6720:('syscon_target_modem_poweroff',1),
    0x347c:('syscon_target_diagnostics_enable',1),0x8fc0:('syscon_target_log_enable',1),
    0x2678:('syscon_target_assert',3),0x591c:('syscon_target_powerkey_mode',1),
    0x8cf0:('syscon_target_uart_available',1),0x8de4:('syscon_target_uart_read',1),0x8c34:('syscon_target_uart_put',2)}
E=0x21008000
def build(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    endpoints=[name for name,_ in DEPENDENCIES.values()]+[n for a,n in ALL_COMMANDS.items() if a not in MAPPINGS]
    trap=destination/'external-endpoints.S';trap.write_text('.syntax unified\n.thumb\n'+''.join(
        f'.global {n}\n.type {n},%function\n.thumb_func\n{n}:\n bkpt #0\n bx lr\n' for n in endpoints))
    old=runtime.SOURCES
    try:
        runtime.SOURCES=old+['src/protocol/control_commands_target.c','tests/fixtures/target/control_commands_test_fixture.c',
            'src/protocol/protocol_target.c','src/protocol/protocol_state.c','src/protocol/command_table_target.c','src/runtime/callback_helpers.c',str(trap)]
        elf=runtime.build(destination)
    finally:runtime.SOURCES=old
    (destination/'control-mappings.json').write_text(json.dumps({'entries':{hex(a):n for a,n in MAPPINGS.items()},
        'source_hash':hashlib.sha256((ROOT/'src/protocol/control_commands_target.c').read_bytes()).hexdigest(),
        'dependencies':{hex(a):n for a,(n,c) in DEPENDENCIES.items()}},indent=2)+'\n')
    return elf
class Original(Oracle):
    def __init__(self,elf,a,pair):
        self.pair=pair;self.redirect={0x8f88:a.symbols['syscon_target_logger'],0x8fa0:a.symbols['syscon_target_mfg_logger']}
        super().__init__();self.cpu.mem_map(a.CODE,0x100000);self.cpu.mem_map(a.DATA,0x10000)
        with Path(elf).open('rb') as f:
            for segment in ELFFile(f).iter_segments():
                if segment['p_type']=='PT_LOAD' and segment['p_filesz']:self.put(segment['p_vaddr'],segment.data())
        self.cpu.mem_protect(a.CODE,0x100000,UC_PROT_READ|UC_PROT_EXEC)
        self.cpu.mem_protect(0,0x10000,UC_PROT_READ|UC_PROT_EXEC)
    def _step(self,uc,address,size,_):
        if address in self.redirect:
            REPLACED_ENDPOINTS.add(address);uc.reg_write(UC_ARM_REG_PC,self.redirect[address]);return
        if address<0x10000:super()._step(uc,address,size,_)
    def read(self,address,size):return bytes(self.cpu.mem_read(address,size))
class Terminal(Exception):pass
class Pair:
    def __init__(self,elf):
        self.a=ArmRebuildOracle(elf);self.o=Original(elf,self.a,self);self.machines=(self.o,self.a)
        self.calls=[[],[]];self.results={0x5dc8:1,0x5df4:0xb6bb,0x5e0c:0xb822};self.writes=[[],[]];self.pending=[bytearray(),bytearray()];self.spin_reset=False
        self.rgb=bytes([5,12,34,56,78,1]);self.pin=1
        for index,m in enumerate(self.machines):
            m.put(E,bytes(0x6000));m.cpu.mem_map(0xe000e000,0x1000)
            for entry,(name,count) in DEPENDENCIES.items():
                hook=lambda machine,entry=entry,count=count,index=index:self.dependency(machine,index,entry,count)
                m.hooks[entry if index==0 else self.a.symbols[name]&~1]=hook
            def record(uc,kind,address,size,value,_,i=index):
                # Original parser->handler->sscanf stack reaches0x20000b7c.
                # Compare persistent state and guards below that stack region.
                if 0x20000000<=address<0x20000b00:self.writes[i].append((address,size,value&((1<<(size*8))-1)))
                if address==0xe000ed0c:
                    self.calls[i].append(('reset',value))
                    if not self.spin_reset:raise Terminal('reset requested')
            m.cpu.hook_add(UC_HOOK_MEM_WRITE,record)
    def dependency(self,m,index,entry,count):
        args=[m.arg(i) for i in range(count)];payload=None
        if entry==0x8cf0:return len(self.pending[index])
        if entry==0x8de4:return self.pending[index].pop(0) if self.pending[index] else 0xffffffff
        if entry==0x39e8:m.put(args[1],bytes([self.pin]));args[1]=0
        elif entry==0x5dc8:m.put(args[0],self.rgb);args[0]=0
        elif entry==0x5c38:payload=m.read(args[0],5);args[0]=0
        elif entry==0x74e8:
            payload=m.read(args[0],args[1]) if args[1]<=128 else None
            args[0]=0
        if entry==0x2678:args=[text_argument(m,args[0]),args[1],text_argument(m,args[2])]
        self.calls[index].append((entry,args,payload))
        if entry==0x2678:raise Terminal('assert')
        if entry==0x4c50:return self.results.get(entry,1000)+args[0]
        return self.results.get(entry,0)
    def put(self,address,data):
        for m in self.machines:m.put(address,data)
    def word(self,address,value):self.put(address,struct.pack('<I',value&0xffffffff))
    def output(self,m):
        events=[]
        for index in range(m.u32(E)):
            data=m.read(E+256+index*192,192)
            words=struct.unpack_from('<16I',data)
            kind,fmt,tag,level,count=words[:5]
            text=data[64:64+words[12]]
            conversions=re.findall(rb'%(?!%)[-+ #0]*[0-9.*]*[hl]*([diuxXscp])',text)
            values=tuple(text_argument(m,words[5+i]) if i<len(conversions) and conversions[i]==b's'
                         else words[5+i] for i in range(count))
            events.append((kind,text,text_argument(m,tag),level,values))
        return events
    def run(self,entry,args=None,terminal=False,raw_pointer=None,spin_reset=False):
        self.spin_reset=spin_reset
        pointer=raw_pointer if raw_pointer is not None else 0 if args is None else 0x20000900
        if args is not None:self.put(pointer,args+b'\0')
        for m in self.machines:
            m.put(E,bytes(4))
            for i,r in enumerate(CALLEE):m.cpu.reg_write(r,0x12345000+i)
        for trace in self.calls+self.writes:trace.clear()
        results=[]
        for m,fn in ((self.o,entry),(self.a,MAPPINGS[entry])):
            try:
                results.append(m.call(fn,pointer,self.a.symbols['fixture_command_printer'],count=20000 if spin_reset else 500000));assert not terminal
            except Terminal as error:
                if not terminal:raise
                results.append(str(error))
            except RuntimeError:
                if not spin_reset or self.calls[len(results)][-1]!=('reset',0x05fa0004):raise
                pc=m.cpu.reg_read(UC_ARM_REG_PC)
                # The terminal PC must be in the two-instruction NOP/branch
                # loop, not a budget exhausted in an unrelated dependency.
                code=m.read(pc-2,6)
                assert b'\x00\xbf' in code or b'\xc0\x46' in code
                assert any((int.from_bytes(code[i:i+2],'little')&0xf800)==0xe000 for i in (0,2,4))
                results.append('reset-spin')
        assert results[0]==results[1]
        if not terminal:
            for m in self.machines:assert [m.cpu.reg_read(r) for r in CALLEE]==[0x12345000+i for i in range(len(CALLEE))]
        self.compare();return results[0]
    def compare(self):
        assert self.calls[0]==self.calls[1]
        assert self.output(self.o)==self.output(self.a)
        assert self.o.read(0x20000000,0xb00)==self.a.read(0x20000000,0xb00)
        assert self.writes[0]==self.writes[1]
