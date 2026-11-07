"""Reconstructed ARM libc parsers vs original, with real helper implementations."""
import random
import struct
import pytest
from oracle import Oracle
from arm_rebuild_oracle import ArmRebuildOracle
from build_runtime_scan_image import build
from test_arm_rebuild import call_original_varargs

INPUT=0x20000300
FMT=0x20000600
OUT=0x20000800
ARGS=0x20000a40
FILE=0x20000b00
REENT=0x20000100
STATE=0x20000700

@pytest.fixture(scope='module')
def scan_elf(tmp_path_factory):return build(tmp_path_factory.mktemp('runtime-scan'))

class Pair:
    def __init__(self,elf):
        self.ref=Oracle();self.arm=ArmRebuildOracle(elf)
        self.put(0x20000258,struct.pack('<I',REENT))
    def put(self,address,data):
        self.ref.put(address,data);self.arm.put(address,data)
    def equal(self,address,size):
        expected=bytes(self.ref.cpu.mem_read(address,size));actual=self.arm.read(address,size)
        assert actual==expected,(hex(address),actual,expected)
    def call(self,entry,symbol,*args):
        # Compare identical original private-stack inputs even though the two
        # relocated CPU stacks live at different addresses and prior C frames differ.
        if entry in (0x976c,0x9b24):
            shift=136 if entry==0x976c else 0
            for offset in [136+shift,104+shift]:
                self.arm.put(self.arm.DATA+0xff00-offset,self.ref.cpu.mem_read(0x20000fc0-offset,4))
        expected=call_original_varargs(self.ref,entry,*args);actual=self.arm.call(symbol,*args)
        assert actual==expected,(hex(entry),args,actual,expected)
        return actual
    def file(self,text,flags=0x204):
        self.put(INPUT,text+b'\0');raw=bytearray(104)
        struct.pack_into('<IIIHHII',raw,0,INPUT,len(text),0,flags,0xffff,INPUT,len(text))
        self.put(FILE,raw)


def test_strtol_core_alias_global_errno_end_pointer_and_all_bases(scan_elf):
    p=Pair(scan_elf);rng=random.Random(0x9904)
    inputs=[b'',b' ',b'\t\r\n-1',b'+',b'-',b'0',b'0x',b'-0x',b'0xg',b'0Xff',b'0778',
            b'2147483647',b'2147483648',b'-2147483648',b'-2147483649',b'4294967295',
            b'-9999999999999999999999999!',b'\x80ABC',b'\xff12',b'zzZZ',b'+0012tail']
    inputs += [rng.randbytes(rng.randrange(1,40)).replace(b'\0',b'x') for _ in range(60)]
    for entry,symbol in [(0x9904,'syscon_rt_strtol_core'),(0x9a20,'syscon_rt_strtol_r'),(0x9a28,'syscon_rt_strtol')]:
        for text in inputs:
            for base in [-1,0,1,*range(2,37),37,0x80000000]:
                for end in [0,OUT]:
                    p.put(INPUT,text+b'\0');p.put(REENT,struct.pack('<I',0x1234));p.put(FILE,struct.pack('<I',0x5678));p.put(OUT,b'\xa5'*4)
                    args=(INPUT,end,base) if entry==0x9a28 else (FILE,INPUT,end,base)
                    p.call(entry,symbol,*args);p.equal(OUT,4);p.equal(REENT,4);p.equal(FILE,4)


def test_strncasecmp_unsigned_bytes_limits_and_stopping(scan_elf):
    p=Pair(scan_elf);rng=random.Random(0x9844)
    pairs=[(bytes([v])+b'AbCd\0',bytes([v^32])+b'aBcD\0') for v in range(256)]
    pairs += [(rng.randbytes(30)+b'\0',rng.randbytes(30)+b'\0') for _ in range(100)]
    for a,b in pairs:
        p.put(INPUT,a);p.put(FMT,b)
        for n in [0,1,2,5,30,0xffffffff]:p.call(0x9844,'syscon_rt_strncasecmp',INPUT,FMT,n)


def test_scanset_ranges_inversion_escapes_and_malformed_terminators(scan_elf):
    p=Pair(scan_elf)
    for text in [b'a-z]',b'^a-z]',b']a-c]',b'-ab]',b'a-c-e]',b'z-a]',b'aa-a]',b'^]',b'',b'^',b'[a]',b'\xff-\xfe]',b'\x80-\xff]',b'abc',b'a-']:
        p.put(FMT,text+b'\0');p.put(OUT,b'\xa5'*256)
        p.call(0xa69c,'syscon_scan_sccl',OUT,FMT);p.equal(OUT,256)


def scan_case(p,text,fmt,wrapper=False,flags=0x204):
    p.file(text,flags);p.put(FMT,fmt+b'\0');p.put(OUT,b'\xa5'*512)
    pointers=[OUT+i*64 for i in range(8)];p.put(ARGS,struct.pack('<8I',*pointers))
    p.put(REENT,struct.pack('<I',123))
    if wrapper:p.call(0x97d4,'syscon_rt_sscanf',INPUT,FMT,*pointers)
    else:p.call(0x9ddc,'syscon_rt_vfscanf',REENT,FILE,FMT,ARGS);p.equal(FILE,104)
    p.equal(OUT,512);p.equal(REENT,4)


def test_sscanf_and_vfscanf_numeric_widths_signs_prefixes_and_overflow(scan_elf):
    p=Pair(scan_elf)
    texts=[b'',b' ',b'-',b'+',b'0x',b'-0x',b'0xg',b'+0XfFtail',b'0779tail',b'12345abc',
           b'-2147483649tail',b'4294967296tail',b'000000000',b'\t -0010,20 03',b'0'*360+b'1',b'9'*360]
    for wrapper in [False,True]:
        for text in texts:
            for fmt in [b'%d%n%c',b'%i%n%c',b'%u%n%c',b'%o%n%c',b'%x%n%c',b'%p%n%c',
                        b'%hd%n',b'%ld%n',b'%hhd%n',b'%lld%n',b'%2i%n%c',b'%1i%n%c',b'%350d%n%c',
                        b'%*d%n%c',b'%d,%u %o%n']:
                scan_case(p,text,fmt,wrapper)


def test_sscanf_and_vfscanf_strings_scansets_literals_suppression_and_eof(scan_elf):
    p=Pair(scan_elf)
    for wrapper in [False,True]:
        for text in [b'',b' ',b'abc def',b'xyz',b'1234',b'aa--zz',b'%abc!',b'\r\nABC\xff',b'abcdef']:
            for fmt in [b'',b' ',b'%s%n',b'%3s%n%c',b'%c%n',b'%4c%n',b'%*c%n%c',b'%[a-z]%n%c',
                        b'%[^0-9]%n',b'%[]a-z]%n',b'%[z-a]%n',b'%% %s',b'abc%n',b'%n',b'%hn',b'%*n',
                        b'%',b'%q%n',b'%f%n%c',b'%E%n%c',b'%F%n%c',b'%G%n%c',b'%A%n',b'%d%n']:
                scan_case(p,text,fmt,wrapper)
    # Input failure after assignment is EOF when the stream already has SERR.
    scan_case(p,b'12',b'%d%c',False,0x244)


def test_nano_snprintf_integer_flags_width_precision_and_truncation(scan_elf):
    p=Pair(scan_elf);rng=random.Random(0x976c)
    p.put(INPUT,b'example-string\0')
    formats=[b'',b'plain',b'%%',b'%cafter',b'%s/%8.3s',b'%*.*d',b'%#08x',b'%p/%n',
             b'%hhd',b'%lld',b'%q',b'%u/%d/%o/%X',b'%+.0d/%#.0o/%#.0x']
    formats += [b'%'+flag+length+spec for flag in [b'',b'#',b'08',b'-12',b'+12.8',b' .0']
                for length in [b'',b'h',b'l',b'L'] for spec in [b'd',b'i',b'u',b'o',b'x',b'X']]
    for fmt in formats:
        values=[INPUT]*8 if b's' in fmt else [rng.getrandbits(32) for _ in range(8)]
        if fmt==b'%*.*d':values=[-12,-1,0x80000000]+[0]*5
        if b'%n' in fmt:values=[0,OUT+200]+[0]*6
        for size in [0,1,2,8,32,128,0x80000000]:
            p.put(FMT,fmt+b'\0');p.put(OUT,b'\xa5'*256);p.put(REENT,struct.pack('<I',77))
            p.call(0x976c,'syscon_rt_snprintf',OUT,size,FMT,*values)
            p.equal(OUT,256);p.equal(REENT,4)


def test_vfprintf_absent_float_handler_exact_seed_and_previous_conversion_result(scan_elf):
    p=Pair(scan_elf)
    for fmt in [b'%f',b'prefix%f suffix',b'%f%f',b'%u/%f/%f/%u',b'%Lf/%d',b'%d/%f']:
        for seed in [0,1,7,0xffffffff,0xfffffffe,0x7fffffff,0x80000000]:
            for capacity in [0,1,8,127]:
                p.put(FMT,fmt+b'\0');p.put(OUT,b'\xa5'*256);p.put(REENT,struct.pack('<I',77))
                p.put(ARGS,struct.pack('<12I',*[0x10000000+i for i in range(12)]))
                raw=bytearray(104);struct.pack_into('<IIIHHII',raw,0,OUT,0,capacity,0x208,0xffff,OUT,capacity)
                p.put(FILE,raw)
                # The original parser's first-conversion n is entrySP-136.
                p.ref.put(0x20000fc0-136,struct.pack('<I',seed));p.ref.put(0x20000fc0-104,bytes(4))
                expected=call_original_varargs(p.ref,0x9b24,REENT,FILE,FMT,ARGS)
                actual=p.arm.call('syscon_rt_vfprintf_seeded',REENT,FILE,FMT,ARGS,seed,0)
                assert actual==expected,(fmt,seed,capacity,actual,expected)
                p.equal(OUT,256);p.equal(FILE,104);p.equal(REENT,4)
    p.put(FMT,b'%f\0')
    assert p.arm.call('syscon_rt_vfprintf_checked',REENT,FILE,FMT,ARGS)==0x80000000


def test_vfprintf_initial_dynamic_buffer_allocation_failure_and_existing_stream_error(scan_elf):
    p=Pair(scan_elf);out=0x20000900
    for flags,base in [(0x280,0),(0x248,out),(0x208,out)]:
        raw=bytearray(104);struct.pack_into('<IIIHHII',raw,0,base,0,16,flags,0xffff,base,16)
        p.put(FILE,raw);p.put(FMT,b'%d\0');p.put(ARGS,struct.pack('<I',123));p.put(out,b'\xa5'*64);p.put(0x20000810,bytes(16))
        p.put(REENT,struct.pack('<I',77))
        p.call(0x9b24,'syscon_rt_vfprintf',REENT,FILE,FMT,ARGS)
        p.equal(FILE,104);p.equal(out,64);p.equal(REENT,4)


def test_scan_helpers_exact_state_and_argument_updates(scan_elf):
    p=Pair(scan_elf)
    # External scan state is deliberately placed in an additional test-only RAM
    # page so all388 bytes plus table and output coexist without targetstack overlap.
    state,table=0x22000000,0x22000200
    for cpu in [p.ref.cpu,p.arm.cpu]:cpu.mem_map(state,4096)
    for code,entry,symbol in [(0,0xa3d8,'syscon_scan_chars'),(1,0xa3d8,'syscon_scan_chars'),
                              (2,0xa3d8,'syscon_scan_chars'),(3,0xa494,'syscon_scan_integer'),(4,0xa494,'syscon_scan_integer')]:
        for text in [b'abc',b'123xyz',b'-0x',b'0xFfZ',b'0000012',b'-2147483649',b' ']:
            for flags in [0,1,2,0x10,0x20,0x200]:
                for width in [0,1,3,350,0xffffffff]:
                    p.file(text);p.put(OUT,b'\xa5'*64);p.put(ARGS,struct.pack('<II',OUT,ARGS+8));p.put(ARGS+8,struct.pack('<I',OUT))
                    # Pointer to the target va_list lives in ARGS+4.
                    raw=bytearray(b'\xa5'*388)
                    struct.pack_into('<7I',raw,0,flags,0,width,3,5,table,code)
                    struct.pack_into('<II',raw,380,0x9d25,0x9d9d)
                    p.put(state,raw);p.put(table,bytes(int(97<=i<=122) for i in range(256)))
                    p.arm.put(state+380,struct.pack('<II',p.arm.symbols['syscon_rt_sungetc_r'],p.arm.symbols['syscon_rt_ssrefill_r']))
                    p.put(REENT,struct.pack('<I',77))
                    p.call(entry,symbol,REENT,state,FILE,ARGS+4)
                    p.equal(FILE,104);p.equal(OUT,64);p.equal(ARGS,12);p.equal(state,380);p.equal(table,256);p.equal(REENT,4)


def test_scan_integration_detects_corrupted_numeric_conversion(scan_elf):
    p=Pair(scan_elf)
    scan_case(p,b'123',b'%d')
    p=Pair(scan_elf)  # fresh CPU: no stale translated block after code mutation
    # Deliberately break the rebuilt numeric converter: movs r0,#0; bx lr.
    p.arm.put(p.arm.symbols['syscon_rt_strtol_core']&~1,b'\x00\x20\x70\x47')
    with pytest.raises(AssertionError):scan_case(p,b'123',b'%d')


def test_original_abi_first_float_stack_seed_direct_and_snprintf_wrapper(scan_elf):
    p=Pair(scan_elf)
    for wrapper in [False,True]:
        for fmt in [b'%f',b'prefix%f suffix',b'%f%f',b'%Lf/%d',b'%d/%f/%u']:
            for seed in [0,7,0xffffffff,0xfffffffe,0x7fffffff,0x80000000]:
                p.put(FMT,fmt+b'\0');p.put(OUT,b'\xa5'*128);p.put(REENT,struct.pack('<I',77))
                words=[0x10000000+i for i in range(10)]
                p.put(ARGS,struct.pack('<10I',*words))
                raw=bytearray(104);struct.pack_into('<IIIHHII',raw,0,OUT,0,127,0x208,0xffff,OUT,127)
                p.put(FILE,raw)
                distance=272 if wrapper else 136
                p.ref.put(0x20000fc0-distance,struct.pack('<I',seed))
                p.arm.put(p.arm.DATA+0xff00-distance,struct.pack('<I',seed))
                if wrapper:p.call(0x976c,'syscon_rt_snprintf',OUT,128,FMT,*words)
                else:p.call(0x9b24,'syscon_rt_vfprintf',REENT,FILE,FMT,ARGS);p.equal(FILE,104)
                p.equal(OUT,128);p.equal(REENT,4)


def test_vfprintf_real_free_list_allocation_and_literal_growth_failure(scan_elf):
    p=Pair(scan_elf)
    # A legitimate initialized free block exercises malloc success with the
    # image's real allocator, without replacing its always-failing sbrk endpoint.
    p.put(0x20000400,struct.pack('<II',512,0)+b'\xa5'*504)
    p.put(0x20000810,struct.pack('<4I',0,0,0x20000400,0))
    raw=bytearray(104);struct.pack_into('<IIIHHII',raw,0,0,0,64,0x280,0xffff,0,0)
    p.put(FILE,raw);p.put(FMT,b'allocated:%d\0');p.put(ARGS,struct.pack('<I',123));p.put(REENT,struct.pack('<I',77))
    p.call(0x9b24,'syscon_rt_vfprintf',REENT,FILE,FMT,ARGS)
    p.equal(FILE,104);p.equal(0x20000400,512);p.equal(0x20000810,16);p.equal(REENT,4)
    # Literal write invokes the real growth path and propagates its failure.
    p=Pair(scan_elf);p.put(0x20000810,bytes(16));out=0x20000900
    raw=bytearray(104);struct.pack_into('<IIIHHII',raw,0,out,0,1,0x600,0xffff,out,1)
    p.put(FILE,raw);p.put(out,b'\xa5'*64);p.put(FMT,b'cannot-grow\0');p.put(REENT,struct.pack('<I',77))
    p.call(0x9b24,'syscon_rt_vfprintf',REENT,FILE,FMT,ARGS)
    p.equal(FILE,104);p.equal(out,64);p.equal(0x20000810,16);p.equal(REENT,4)


def test_original_abi_initial_octal_size_stack_seed_and_later_size_reuse(scan_elf):
    p=Pair(scan_elf)
    for wrapper in [False,True]:
        for fmt in [b'%#o',b'%#.0o',b'%#.3o',b'%#8.5o',b'%u/%#o',b'%s/%#.3o',b'%f/%#o']:
            for size_seed in [0,1,3,8,0xffffffff,0x80000000,0x7fffffff]:
                for value in [0,1,7,8,0xffffffff]:
                    p.put(FMT,fmt+b'\0');p.put(OUT,b'\xa5'*128);p.put(REENT,struct.pack('<I',77));p.put(INPUT,b'example\0')
                    words=[INPUT if b'%s' in fmt else value]+[value]*9
                    p.put(ARGS,struct.pack('<10I',*words))
                    raw=bytearray(104);struct.pack_into('<IIIHHII',raw,0,OUT,0,127,0x208,0xffff,OUT,127)
                    p.put(FILE,raw);shift=136 if wrapper else 0
                    p.ref.put(0x20000fc0-(136+shift),struct.pack('<I',9))
                    p.ref.put(0x20000fc0-(104+shift),struct.pack('<I',size_seed))
                    if wrapper:p.call(0x976c,'syscon_rt_snprintf',OUT,128,FMT,*words)
                    else:p.call(0x9b24,'syscon_rt_vfprintf',REENT,FILE,FMT,ARGS);p.equal(FILE,104)
                    p.equal(OUT,128);p.equal(REENT,4)
