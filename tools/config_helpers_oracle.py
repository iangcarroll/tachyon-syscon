"""Build original-ABI config bodies, source-backed runtime and FLASHCTL path."""
from pathlib import Path
import struct
import re
from unicorn import UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
from arm_rebuild_oracle import REGISTERS
from oracle import Oracle
from arm_rebuild_oracle import ArmRebuildOracle
import build_runtime_scan_image as runtime

def read_string(cpu, address, limit=1024):
    """Read a defined string argument; never normalize arbitrary integer values."""
    value=bytearray()
    for offset in range(limit):
        byte=cpu.cpu.mem_read(address+offset,1)[0]
        if not byte:return bytes(value)
        value.append(byte)
    raise AssertionError('Unterminated string argument')


def logger_arguments(cpu):
    """Compare logger text and typed varargs independently of linker placement."""
    fmt=read_string(cpu,cpu.arg(2))
    tokens=re.findall(rb'%(?:%|[-+ #0]*[0-9]*(?:\.[0-9]+)?[diuxXscp])',fmt)
    assert b'%' not in re.sub(rb'%(?:%|[-+ #0]*[0-9]*(?:\.[0-9]+)?[diuxXscp])',b'',fmt),fmt
    args=[]
    for token in tokens:
        if token==b'%%':continue
        value=cpu.arg(3+len(args))
        args.append(read_string(cpu,value) if token[-1:]==b's' else value)
    return (cpu.arg(0),read_string(cpu,cpu.arg(1)),fmt,*args)


TRAPS=('syscon_cfg_assert',)
def build(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    traps=destination/'config_unresolved.S'
    traps.write_text('.syntax unified\n.thumb\n'+''.join(
        f'.global {name}\n.type {name},%function\n.thumb_func\n{name}:\n bkpt #0\n bx lr\n' for name in TRAPS))
    old=runtime.SOURCES
    try:
        runtime.SOURCES=old+['target/config/config_helpers.c','target/config/config_read.c','target/config/config_storage.c','target/config/config_update.c','src/flash_controller.c','src/format.c','src/logging.c','target/testing/format_wrappers.c','target/logging/logger_target.c','target/logging/logger_state.c','target/logging/logger_target_abi.S',str(traps)]
        return runtime.build(destination)
    finally:runtime.SOURCES=old

class ConfigHelperPair:
    owners=None
    def __init__(self,elf):
        if self.owners is not None:self.owners.append(self)
        self.original=Oracle();self.candidate=ArmRebuildOracle(elf)
        self.events=[[],[]]
        for index,cpu in enumerate((self.original,self.candidate)):
            cpu.cpu.mem_map(0x40081000,4096)
            def write(uc,access,address,size,value,user,index=index):self.events[index].append(('mmio-write',address,size,value))
            cpu.cpu.hook_add(UC_HOOK_MEM_WRITE,write,begin=0x40081000,end=0x40081fff)
        self.put(0x20000258,struct.pack('<I',0x20000280))
    def put(self,address,data):
        for cpu in (self.original,self.candidate):cpu.put(address,data)
    def equal(self,address,size):
        left=bytes(self.original.cpu.mem_read(address,size));right=self.candidate.read(address,size)
        assert left==right,(hex(address),left,right)
    def bind(self,address,symbol,callback):
        for index,(cpu,entry) in enumerate(((self.original,address),(self.candidate,self.candidate.symbols[symbol]&~1))):
            cpu.hooks[entry]=lambda oracle,index=index:callback(oracle,self.events[index])
    def call(self,address,symbol,*args,returns=True,same_stack=False):
        expected=self.original.call(address,*args,count=1000000)
        if same_stack:
            cpu=self.candidate;sp=0x20000ff0
            cpu.cpu.reg_write(UC_ARM_REG_SP,sp);cpu.cpu.reg_write(UC_ARM_REG_LR,cpu.SENTINEL|1)
            for i,value in enumerate(args):
                if i<4:cpu.cpu.reg_write(REGISTERS[i],value&0xffffffff)
                else:cpu.put(sp+4*(i-4),struct.pack('<I',value&0xffffffff))
            cpu.cpu.emu_start(cpu.symbols[symbol]|1,cpu.SENTINEL,count=1000000)
            assert cpu.cpu.reg_read(UC_ARM_REG_PC)==cpu.SENTINEL
            actual=cpu.cpu.reg_read(REGISTERS[0])
        else:actual=self.candidate.call(symbol,*args,count=1000000)
        if returns:assert actual==expected,(hex(address),args,actual,expected)
        assert self.events[0]==self.events[1],(hex(address),self.events)
        return actual
