"""ARM-vs-ARM tests for recovered heap/FILE routines, no host libc oracle."""
import struct
import subprocess
from pathlib import Path
import toolchain_process
from oracle import Oracle
ROOT=Path(__file__).resolve().parents[1]
CODE=0x01000000
HEAP=0x21000000
HEAP_SIZE=0x10000
REENT=0x20000840
class RuntimeImage:
    def __init__(self,directory):
        directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
        sources=[ROOT/'target/runtime_heap.c',ROOT/'target/runtime_stdio.c',ROOT/'src/runtime_memory.c',ROOT/'target/runtime_support.c',ROOT/'src/runtime_arithmetic.c',ROOT/'target/runtime_arithmetic_abi.S']
        flags=['-std=c11','-mcpu=cortex-m0plus','-mthumb','-Os','-ffreestanding','-fno-builtin','-fno-inline','-fno-ipa-cp','-fno-ipa-pure-const','-ffunction-sections','-fdata-sections','-Wall','-Wextra','-Werror','-I'+str(ROOT/'include')]
        objects=[]
        for i,source in enumerate(sources):
            obj=directory/f'{i}.o';toolchain_process.run(['arm-none-eabi-gcc',*flags,*(['-O2'] if source.name=='runtime_arithmetic.c' else []),'-c',str(source),'-o',str(obj)],check=True);objects.append(str(obj))
        retained=[]
        for obj in objects[:2]:
            for line in toolchain_process.check_output(['arm-none-eabi-nm',obj],text=True).splitlines():
                fields=line.split()
                if len(fields)==3 and fields[1] in ('T','W'):retained.append('-Wl,--undefined='+fields[2])
        elf=directory/'runtime.elf';binary=directory/'runtime.bin'
        toolchain_process.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib','-Wl,-Ttext=0x01000000','-Wl,-e,syscon_rt_malloc_r','-Wl,--gc-sections',*retained,*objects,'-o',str(elf)],check=True)
        toolchain_process.run(['arm-none-eabi-objcopy','-O','binary',str(elf),str(binary)],check=True)
        self.code=binary.read_bytes();self.symbols={}
        for line in toolchain_process.check_output(['arm-none-eabi-nm',str(elf)],text=True).splitlines():
            fields=line.split()
            if len(fields)==3:self.symbols[fields[2]]=int(fields[0],16)
class RuntimeOracle(Oracle):
    def __init__(self,image=None):
        super().__init__();self.runtime_image=image;self.cpu.mem_map(HEAP,HEAP_SIZE)
        self.put(HEAP,bytes((i*71+19)&255 for i in range(HEAP_SIZE)))
        if image:
            self.cpu.mem_map(CODE,(len(image.code)+4095)&~4095);self.put(CODE,image.code)
    def run(self,name,original,*args,count=200000):
        return self.call(self.runtime_image.symbols[name] if self.runtime_image else original,*args,count=count)
class ScriptedBreak:
    """Explicit hypothetical sbrk backing; stock image always returns -1."""
    def __init__(self,oracle,start=HEAP+3,limit=HEAP+HEAP_SIZE,fail_at=None,errno=0):
        self.oracle=oracle;self.current=start;self.limit=limit;self.calls=[];self.fail_at=fail_at;self.errno=errno
        entry=oracle.runtime_image.symbols['syscon_rt_sbrk'] if oracle.runtime_image else 0x76f0
        oracle.hooks[entry]=self.call
    def call(self,o):
        increment=struct.unpack('<i',struct.pack('<I',o.arg(0)))[0];old=self.current
        fail=len(self.calls)==self.fail_at or old+increment>self.limit or old+increment<HEAP
        result=0xffffffff if fail else old
        if fail:o.put(0x20000810,struct.pack('<I',self.errno))
        else:self.current+=increment
        self.calls.append((increment,result,self.errno if fail else 0));return result
class RuntimePair:
    def __init__(self,image,backing=False,**kwargs):
        self.original=RuntimeOracle();self.candidate=RuntimeOracle(image)
        self.breaks=[ScriptedBreak(o,**kwargs) for o in (self.original,self.candidate)] if backing else []
        for o in (self.original,self.candidate):o.put(REENT,b'\x5a'*32)
    def put(self,address,data):
        for o in (self.original,self.candidate):o.put(address,data)
    def run(self,name,address,*args,count=200000):
        expected=self.original.run(name,address,*args,count=count)
        actual=self.candidate.run(name,address,*args,count=count)
        assert actual==expected,(name,args,hex(actual),hex(expected))
        self.compare();return actual
    def compare(self):
        for address,size in [(0x20000810,16),(REENT,32),(HEAP,HEAP_SIZE)]:
            a=bytes(self.original.cpu.mem_read(address,size));b=bytes(self.candidate.cpu.mem_read(address,size))
            assert a==b,('memory',hex(address),next((i for i,(x,y) in enumerate(zip(a,b)) if x!=y),None))
        if self.breaks:assert self.breaks[0].calls==self.breaks[1].calls
