import random
import struct
from pathlib import Path
import pytest
from elftools.elf.elffile import ELFFile
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_WRITE,UC_PROT_READ,UC_PROT_EXEC,UcError
from unicorn.arm_const import UC_ARM_REG_R1,UC_ARM_REG_PRIMASK
from arm_rebuild_oracle import ArmRebuildOracle
from oracle import Oracle
from ioexpander_target_oracle import CALLEE
from build_format_core_target import build,MAPPINGS
E=0x21008000
FMT=0x20000800
ARGS=0x20000900
STRING=0x20000a20

@pytest.fixture(scope='module')
def format_core_elf(tmp_path_factory):return build(tmp_path_factory.mktemp('format-core-target')/'test.elf')

class Original(Oracle):
    def __init__(self,elf,a):
        super().__init__();self.cpu.mem_map(a.CODE,0x100000);self.cpu.mem_map(a.DATA,0x10000)
        with Path(elf).open('rb') as f:
            for segment in ELFFile(f).iter_segments():
                if segment['p_type']=='PT_LOAD' and segment['p_filesz']:self.put(segment['p_vaddr'],segment.data())
        self.cpu.mem_protect(a.CODE,0x100000,UC_PROT_READ|UC_PROT_EXEC)
        self.cpu.mem_protect(0,0x10000,UC_PROT_READ|UC_PROT_EXEC)
    def _step(self,uc,address,size,_):
        if address<0x10000:super()._step(uc,address,size,_)
    def read(self,address,size):return bytes(self.cpu.mem_read(address,size))
class Pair:
    def __init__(self,elf):
        self.a=ArmRebuildOracle(elf);self.o=Original(elf,self.a);self.machines=(self.o,self.a);self.writes=[[],[]]
        for i,m in enumerate(self.machines):
            m.put(E,bytes(8192))
            def record(uc,kind,address,size,value,_,index=i):
                if 0x20000000<=address<0x20000d00:self.writes[index].append((address,size,value&((1<<(8*size))-1)))
            m.cpu.hook_add(UC_HOOK_MEM_WRITE,record)
    def put(self,address,data):
        for m in self.machines:m.put(address,data)
    def word(self,address,value):self.put(address,struct.pack('<I',value))
    def calls(self,m):return m.read(E+128,m.u32(E)*8)
    def run(self,entry,*args):
        for m in self.machines:
            m.put(E,bytes(4));m.cpu.reg_write(UC_ARM_REG_PRIMASK,1)
            for i,r in enumerate(CALLEE):m.cpu.reg_write(r,0x34567890+i)
        for trace in self.writes:trace.clear()
        x=self.o.call(entry,*args);y=self.a.call(MAPPINGS[entry],*args)
        assert x==y
        if entry==0x8fcc:assert self.o.cpu.reg_read(UC_ARM_REG_R1)==self.a.cpu.reg_read(UC_ARM_REG_R1)==args[2]
        assert self.o.read(0x20000000,0xd00)==self.a.read(0x20000000,0xd00)
        assert self.writes[0]==self.writes[1]
        assert self.calls(self.o)==self.calls(self.a)
        for m in self.machines:
            assert [m.cpu.reg_read(r) for r in CALLEE]==[0x34567890+i for i in range(len(CALLEE))]
            assert m.cpu.reg_read(UC_ARM_REG_PRIMASK)==1
        return x

def test_numeric_digits_all_radices_signed_remainder_alphabet_byte_and_pair_return(format_core_elf):
    p=Pair(format_core_elf);rng=random.Random(0x8fcc)
    values=[0,1,9,10,0xffffffff,0x100000000,0x8000000000000000,0xffffffffffffffff]+[rng.getrandbits(64) for _ in range(20)]
    for radix in (2,3,8,10,16,36,255,0x7fffffff,0x80000000,0xffffffff):
        for alphabet in (0,32,255,0x12345678):
            for value in values:
                p.put(FMT,b'\xa5'*128)
                p.run(0x8fcc,value&0xffffffff,value>>32,FMT,radix,alphabet)

@pytest.mark.parametrize('radix,value',[(0,0),(0,0x123456789abcdef0),(1,1)])
def test_degenerate_radix_runs_to_buffer_fault_instead_of_added_validation(format_core_elf,radix,value):
    p=Pair(format_core_elf);buffer=0x20000ff8
    for m,entry in ((p.o,0x8fcc),(p.a,MAPPINGS[0x8fcc])):
        with pytest.raises(UcError):m.call(entry,value&0xffffffff,value>>32,buffer,radix,32)
    assert p.o.read(buffer,8)==p.a.read(buffer,8)

def test_forward_actual_callback_return_count_wrap_and_mutated_function_context(format_core_elf):
    p=Pair(format_core_elf);ctx=ARGS
    for count in (0,1,0xfffffffe,0xffffffff):
        p.put(ctx,struct.pack('<III',p.a.symbols['fixture_char_sink'],ctx,count))
        p.word(E+4,1);p.word(E+8,0x87654321);p.word(E+12,p.a.symbols['fixture_char_alternate'])
        for character in (0,255,0x12345678,0xffffffff):assert p.run(0x9028,character,ctx)==0x87654321

def test_forward_ordered_loads_stores_and_fault_after_increment(format_core_elf):
    p=Pair(format_core_elf);traces=[[],[]];ctx=ARGS
    for i,m in enumerate(p.machines):
        def record(uc,kind,address,size,value,_,index=i):
            if ctx<=address<ctx+12:
                v=value if kind==UC_MEM_WRITE else int.from_bytes(uc.mem_read(address,size),'little')
                traces[index].append((kind,address,size,v))
        m.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,record)
    p.put(ctx,struct.pack('<III',p.a.symbols['fixture_char_sink'],0xabcdef00,0xffffffff));p.run(0x9028,0x87654321,ctx)
    assert traces[0]==traces[1]
    # Count lives in valid SRAM; callback and context words lie below SRAM.
    p=Pair(format_core_elf);p.word(0x20000000,0xffffffff)
    for m,entry in ((p.o,0x9028),(p.a,MAPPINGS[0x9028])):
        with pytest.raises(UcError):m.call(entry,7,0x1ffffff8)
        assert m.u32(0x20000000)==0

def test_callback_formatter_full_conversion_matrix_actual_arm_word_loads(format_core_elf):
    p=Pair(format_core_elf);rng=random.Random(0x9038);p.word(E+8,0xdeadbeef)
    for alignment in (0,4):
        for spec in (b'd',b'i',b'u',b'o',b'x',b'X',b'p',b'c'):
            for length in (b'',b'h',b'hh',b'l',b'll',b'j',b'z',b't'):
                for flags in (b'',b'#+ ',b' +#'):
                    p.put(FMT,b'a%'+flags+length+spec+b'/%u!\0');p.put(ARGS,rng.randbytes(64))
                    p.run(0x9038,p.a.symbols['fixture_char_sink'],0xa5a5f00d,FMT,ARGS+alignment)
    p.put(STRING,b'ABCDE\0');p.put(ARGS,struct.pack('<8I',*([STRING]*8)))
    for fmt in (b'',b'%',b'%#',b'%s/%ls',b'%03d %.2f %f %-s',b'%% %q %n',b'\xff%c%u\x80'):
        p.put(FMT,fmt+b'\0');p.run(0x9038,p.a.symbols['fixture_char_sink'],0,FMT,ARGS)

def test_string_prescan_and_future_format_argument_mutation_with_real_callbacks(format_core_elf):
    p=Pair(format_core_elf);p.put(FMT,b'%s\0');p.put(STRING,b'ABCDE\0');p.word(ARGS,STRING)
    p.word(E+4,2);p.word(E+16,STRING);assert p.run(0x9038,p.a.symbols['fixture_char_sink'],0,FMT,ARGS)==5
    assert bytes(c for c,_ in struct.iter_unpack('<II',p.calls(p.a)))==b'A\0XDE'
    p.word(E+4,3);p.word(E+16,FMT);p.word(E+20,ARGS);p.put(FMT,b'X%u\0');p.word(ARGS,1)
    p.run(0x9038,p.a.symbols['fixture_char_sink'],0,FMT,ARGS)
    assert bytes(c for c,_ in struct.iter_unpack('<II',p.calls(p.a)))==b'X1234abcd'
    p.word(E+4,0);p.put(FMT,b'%cX\0');p.word(ARGS,0);p.run(0x9038,p.a.symbols['fixture_char_sink'],0,FMT,ARGS)
    assert bytes(c for c,_ in struct.iter_unpack('<II',p.calls(p.a)))==b'\0X'

def test_argument_reads_are_words_and_alignment_skips_to_eight_bytes(format_core_elf):
    p=Pair(format_core_elf);traces=[[],[]]
    for i,m in enumerate(p.machines):
        def record(uc,kind,address,size,value,_,index=i):
            if ARGS<=address<ARGS+32:traces[index].append((address,size))
        m.cpu.hook_add(UC_HOOK_MEM_READ,record)
    p.put(FMT,b'%u/%llu\0');p.put(ARGS,struct.pack('<8I',*range(8)))
    p.run(0x9038,p.a.symbols['fixture_char_sink'],0,FMT,ARGS)
    assert traces[0]==traces[1]==[(ARGS,4),(ARGS+8,4),(ARGS+12,4)]

def test_invalid_callback_and_variadic_or_string_memory_faults_are_not_swallowed(format_core_elf):
    for fmt,arg,callback in [(b'%u',0x20000ffd,None),(b'%s',ARGS,None),(b'X',ARGS,0x30000001)]:
        p=Pair(format_core_elf);p.put(FMT,fmt+b'\0');p.word(ARGS,0x30000000)
        cb=callback if callback is not None else p.a.symbols['fixture_char_sink']
        for m,entry in ((p.o,0x9038),(p.a,MAPPINGS[0x9038])):
            with pytest.raises(UcError):m.call(entry,cb,0,FMT,arg)
    p=Pair(format_core_elf);p.put(FMT,b'\0');assert p.run(0x9038,0,0,FMT,0x30000000)==0
