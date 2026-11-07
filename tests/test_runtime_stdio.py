import random
import struct
import pytest
from heap_stdio_oracle import RuntimeImage,RuntimePair,REENT,HEAP
FILE=0x20000880
DATA=0x20000980
END=0x20000870
@pytest.fixture(scope='module')
def stdio_image(tmp_path_factory):return RuntimeImage(tmp_path_factory.mktemp('stdio-arm'))
def compare_region(p,address,size):assert bytes(p.original.cpu.mem_read(address,size))==bytes(p.candidate.cpu.mem_read(address,size))
def stream(p,base,size,position=0,flags=0):
    fields=[0]*26;fields[0]=base+position;fields[2]=size-position;fields[3]=flags;fields[4]=base;fields[5]=size
    p.put(FILE,struct.pack('<26I',*fields))
def invoke(p,name,address,*args):
    result=p.run(name,address,*args);compare_region(p,FILE,104);return result

def test_strtoul_original_base_prefix_overflow_sign_and_endptr(stdio_image):
    p=RuntimePair(stdio_image);rng=random.Random(0xa714)
    samples=[b'',b'0',b'-0',b'+',b'  -1tail',b'0x',b'-0xZ',b'4294967295',b'4294967296',b'-4294967296',b'0777',b'0Xabcdef',b'zzzzzzzzzzzz',b'\xff1',b'\t\n\v\f\r 123']
    samples += [bytes(rng.choice(b'0123456789abcdefABCDEFxyzXYZ-+ \t') for _ in range(rng.randrange(50))) for _ in range(150)]
    for text in samples:
        for base in [-1,0,1,2,8,10,16,36,37]:
            p.put(DATA,text+b'\0');p.put(END,b'\xa5'*4)
            p.run('syscon_rt_strtoul_r',0xa714,REENT,DATA,END,base);compare_region(p,END,4)
    p.run('syscon_rt_strtoul_r',0xa714,REENT,DATA,0,10)

def test_string_writer_fixed_growth_truncation_and_failures(stdio_image):
    for backing in [False,True]:
        for flags in [0,0x400,0x80]:
            p=RuntimePair(stdio_image,backing)
            base=p.run('syscon_rt_malloc_r',0xa980,REENT,32) if flags==0x80 and backing else HEAP+0x8000
            if flags==0x80 and not backing:continue
            p.put(base,b'old'+bytes(29));stream(p,base,32,3,flags)
            for data in [b'',b'x',b'a'*27,b'b'*64,b'\0\xff'*90]:
                p.put(DATA,data)
                result=invoke(p,'syscon_rt_swrite',0x9a60,REENT,FILE,DATA,len(data))
                if result==0xffffffff:break
    # A failed realloc frees the old dynamically allocated buffer before erroring.
    p=RuntimePair(stdio_image,True,limit=HEAP+100)
    base=p.run('syscon_rt_malloc_r',0xa980,REENT,16);stream(p,base,16,0,0x80)
    p.put(DATA,b'x'*200);invoke(p,'syscon_rt_swrite',0x9a60,REENT,FILE,DATA,200)

def test_file_ungetc_inline_dynamic_growth_and_refill(stdio_image):
    for backing in [False,True]:
        p=RuntimePair(stdio_image,backing);stream(p,HEAP+0x8000,32,4,0x20)
        p.put(HEAP+0x8000,b'abcd'+bytes(28));p.put(FILE+4,struct.pack('<I',7))
        for value in [-1,ord('d'),ord('X'),0,255,256,ord('Y'),ord('Z')]:
            result=invoke(p,'syscon_rt_sungetc_r',0x9d24,REENT,value,FILE)
            if result==0xffffffff and value!=-1:break
        invoke(p,'syscon_rt_ssrefill_r',0x9d9c,REENT,FILE)
        p.put(FILE+64,struct.pack('<I',0));invoke(p,'syscon_rt_ssrefill_r',0x9d9c,REENT,FILE)
    p=RuntimePair(stdio_image,True);stream(p,HEAP+0x8000,32)
    for i in range(1050):invoke(p,'syscon_rt_sungetc_r',0x9d24,REENT,65+i%26,FILE)
    invoke(p,'syscon_rt_ssrefill_r',0x9d9c,REENT,FILE)

STATE=0x20000900
AP=0x20000874
ARGS=0x20000b00
WRITER=0x10010

def printf_pair(image,code,flags,precision,width,value,sign=0,fail_at=None,response=0,common=False):
    p=RuntimePair(image);state=bytearray((i*19+7)&255 for i in range(96))
    struct.pack_into('<6I',state,0,flags,precision&0xffffffff,0,width&0xffffffff,0,0x12345678)
    state[24]=code;state[25]=32;state[26]=48;state[67]=sign;state[69]=ord('x')
    p.put(STATE,state);p.put(DATA,b'hello\0extra\0');p.put(ARGS,struct.pack('<4I',value,0x87654321,0,0));p.put(AP,struct.pack('<I',ARGS))
    traces=[[],[]]
    for oracle,trace in zip((p.original,p.candidate),traces):
        def writer(o,trace=trace):
            args=(o.arg(0),o.arg(1),bytes(o.cpu.mem_read(o.arg(2),o.arg(3))))
            result=-1 if len(trace)==fail_at else response;trace.append((args,result));return result
        oracle.hooks[WRITER]=writer
    if common:
        struct.pack_into('<I',state,8,value&0xffffffff);struct.pack_into('<I',state,16,code)
        p.put(STATE,state)
        result=p.run('syscon_rt_printf_common',0xa0d4,REENT,STATE,AP,FILE,WRITER|1)
    else:result=p.run('syscon_rt_printf_integer',0xa1b4,REENT,STATE,FILE,WRITER|1,AP)
    compare_region(p,STATE,96);compare_region(p,AP,4);compare_region(p,DATA,32)
    assert traces[0]==traces[1],(code,flags,precision,width,value,sign,traces)
    return result,traces[0]

def test_printf_common_padding_prefix_and_writer_failures(stdio_image):
    for flags in [0,1,2,4,6,0x20,0x24,0x22]:
        for size,precision,width in [(0,0,0),(3,0,12),(3,8,12),(10,1,4)]:
            for sign in [0,ord('+')]:
                _,trace=printf_pair(stdio_image,size,flags,0,width,precision,sign,common=True)
                for index in range(len(trace)):
                    printf_pair(stdio_image,size,flags,0,width,precision,sign,fail_at=index,common=True)

def test_printf_integer_conversion_flags_varargs_and_writer_failures(stdio_image):
    rng=random.Random(0xa1b4)
    for code in [0,ord('c'),ord('d'),ord('i'),ord('o'),ord('u'),ord('p'),ord('x'),ord('X'),ord('s'),ord('n'),ord('?'),255]:
        for flags in [0,1,2,4,6,7,0x20,0x40,0x80,0xc0]:
            for value in [0,0xffffffff,0x80000000,0x1234]:
                if code in [ord('s'),ord('n')]:value=DATA
                precision=rng.choice([-1,0,1,5]);width=rng.choice([-4,0,4,16]);sign=rng.choice([0,ord('+'),32])
                _,trace=printf_pair(stdio_image,code,flags,precision,width,value,sign)
                if trace:printf_pair(stdio_image,code,flags,precision,width,value,sign,fail_at=rng.randrange(len(trace)))
                printf_pair(stdio_image,code,flags,precision,width,value,sign,response=-2)

def test_integer_format_writer_heap_pipeline_preserves_full_file_and_arena(stdio_image):
    for backing,fail_at in [(False,None),(True,None),(True,1),(True,3),(True,5)]:
        p=RuntimePair(stdio_image,backing,fail_at=fail_at)
        stream(p,HEAP+0x8000,16,3,0x400);p.put(HEAP+0x8000,b'old'+bytes(13))
        for code,value,width in [(ord('d'),0x80000000,32),(ord('x'),0xabcdef01,20),(ord('s'),DATA,80),(ord('n'),DATA,0)]:
            state=bytearray(96);struct.pack_into('<6I',state,0,1,0xffffffff,0,width,0,37)
            state[24]=code;state[25]=32;state[26]=48
            p.put(STATE,state);p.put(DATA,b'test-string\0');p.put(AP,struct.pack('<I',ARGS));p.put(ARGS,struct.pack('<I',value))
            expected=p.original.call(0xa1b4,REENT,STATE,FILE,0x9a61,AP)
            got=p.candidate.run('syscon_rt_printf_integer',0xa1b4,REENT,STATE,FILE,stdio_image.symbols['syscon_rt_swrite']|1,AP)
            assert got==expected;p.compare();compare_region(p,FILE,104);compare_region(p,STATE,96);compare_region(p,AP,4);compare_region(p,DATA,32)
            if got==0xffffffff:break
