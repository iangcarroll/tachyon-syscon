"""Original formatter callbacks remain executable; only the user sink is hooked."""
import ctypes as C
import random
import struct
from oracle import Oracle
from test_format import READ, Memory, Result

CALL=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32)
class Output(C.Structure):
    _fields_=[('callback',C.c_uint32),('context',C.c_uint32),('count',C.c_uint32)]
CALLBACK=0x10041
FMT=0x20000800
ARGS=0x20000900
STRING=0x20000a20


def test_callback_forward_preserves_full_character_and_preincrements_wrapping_count(lib):
    lib.syscon_format_forward.argtypes=[C.POINTER(Output),C.c_uint32,CALL,C.c_void_p]
    for initial in [0,1,0xfffffffe,0xffffffff]:
        o=Oracle();address=0x20000800;events=[];native=[]
        state=Output(CALLBACK,0xcafef00d,initial)
        o.put(address,bytes(state))
        def sink(cpu):
            events.append((cpu.u32(address),cpu.arg(0),cpu.arg(1),cpu.u32(address+8)))
            # The user callback can change the next invocation's state.
            cpu.put(address,struct.pack('<III',cpu.u32(address)^0x10,cpu.arg(1)^0x12345678,(cpu.u32(address+8)+7)&0xffffffff))
            return 0xabcdef01
        o.hooks[CALLBACK&~1]=sink;o.hooks[(CALLBACK^0x10)&~1]=sink
        def native_sink(_,callback,character,context):
            native.append((callback,character,context,state.count))
            state.callback^=0x10;state.context^=0x12345678;state.count=(state.count+7)&0xffffffff
        cb=CALL(native_sink)
        for character in [0,255,0x12345678,0xffffffff]:
            o.call(0x9028,character,address)
            lib.syscon_format_forward(C.byref(state),character,cb,None)
            assert bytes(state)==bytes(o.cpu.mem_read(address,12))
        assert native==events


def run_callback(lib,format,args,alignment=0,mutation=None):
    o=Oracle();events=[];native=[];arg=ARGS+alignment
    o.put(FMT,format+b'\0');o.put(arg,args.ljust(128,b'\0'));o.put(STRING,b'ABCDE\0')
    ram=bytearray(o.cpu.mem_read(0x20000000,4096))
    def target_write(address,data):o.put(address,data)
    def native_write(address,data):ram[address-0x20000000:address-0x20000000+len(data)]=data
    def sink(cpu):
        events.append((CALLBACK,cpu.arg(0),cpu.arg(1)))
        if mutation:mutation(len(events),target_write,arg)
        return 0xdeadbeef  # ignored by the formatter
    o.hooks[CALLBACK&~1]=sink
    expected=o.call(0x9038,CALLBACK,0xa5a5f00d,FMT,arg)
    def read(_,address,p):
        if address<len(o.image):p[0]=o.image[address];return 1
        if 0x20000000<=address<0x20001000:p[0]=ram[address-0x20000000];return 1
        return 0
    def native_sink(_,callback,character,context):
        native.append((callback,character,context))
        if mutation:mutation(len(native),native_write,arg)
    read_cb=READ(read);cb=CALL(native_sink);memory=Memory(read_cb,None)
    lib.syscon_vformat_callback.argtypes=[C.c_uint32,C.c_uint32,CALL,C.c_void_p,C.c_uint32,C.c_uint32,C.POINTER(Memory)]
    lib.syscon_vformat_callback.restype=Result
    result=lib.syscon_vformat_callback(CALLBACK,0xa5a5f00d,cb,None,FMT,arg,C.byref(memory))
    assert result.complete
    assert result.length==expected==len(events)
    assert native==events,(format,native,events)
    return bytes(x[1] for x in native)


def test_callback_formatter_integer_strings_alignment_and_binary_output(lib):
    rng=random.Random(0x9028)
    for alignment in [0,4]:
        for spec in [b'd',b'i',b'u',b'o',b'x',b'X',b'p',b'c']:
            for length in [b'',b'h',b'hh',b'l',b'll',b'j',b'z',b't']:
                for flags in [b'',b'#+ ',b' +#']:
                    args=struct.pack('<8I',*[rng.getrandbits(32) for _ in range(8)])
                    run_callback(lib,b'a%'+flags+length+spec+b'/%u!',args,alignment)
    for f in [b'',b'%',b'%#',b'%s/%ls',b'%03d %.2f %f %-s',b'%% %q %n',b'\xff%c%u\x80']:
        run_callback(lib,f,struct.pack('<8I',*([STRING]*8)))
    assert run_callback(lib,b'%cX',struct.pack('<I',0))==b'\0X'


def test_callback_string_length_is_measured_before_emission(lib):
    def mutate(n,write,arg):
        if n==1:write(STRING+1,b'\0XDEmore\0')
    # Prescanning means the new embedded NUL is emitted, but extension is ignored.
    assert run_callback(lib,b'%s',struct.pack('<I',STRING),mutation=mutate)==b'A\0XDE'


def test_callback_observes_future_format_and_argument_mutations(lib):
    def mutate(n,write,arg):
        if n==1:write(FMT+1,b'%x');write(arg,struct.pack('<I',0x1234abcd))
    assert run_callback(lib,b'X%u',struct.pack('<I',1),mutation=mutate)==b'X1234abcd'


def test_callback_missing_memory_stops_at_explicit_host_boundary(lib):
    lib.syscon_vformat_callback.argtypes=[C.c_uint32,C.c_uint32,CALL,C.c_void_p,C.c_uint32,C.c_uint32,C.POINTER(Memory)]
    lib.syscon_vformat_callback.restype=Result
    for format,arguments in [(b'%u\0',b''),(b'%s\0',struct.pack('<I',STRING)),(b'%c\0',b'\x01\x02'),(b'A%',b'')]:
        events=[];mapping=dict(enumerate(format,FMT));mapping.update(enumerate(arguments,ARGS))
        def read(_,address,p):
            if address not in mapping:return 0
            p[0]=mapping[address];return 1
        read_cb=READ(read);sink=CALL(lambda _,callback,character,context:events.append(character));memory=Memory(read_cb,None)
        result=lib.syscon_vformat_callback(CALLBACK,0,sink,None,FMT,ARGS,C.byref(memory))
        assert not result.complete
        assert events==([ord('A')] if format.startswith(b'A') else [])


def test_logger_prefix_exact_capacity_does_not_overread(lib):
    from test_logging import IO, WRITE, NOW, COLOR, memory_for
    from unicorn.arm_const import UC_ARM_REG_R1
    lib.syscon_logger.argtypes=[C.POINTER(Memory),C.POINTER(IO),C.c_uint8,*([C.c_uint32]*4)]
    for length in [24,25,26]:
        o=Oracle();events=[];native=[]
        o.put(0x2000080c,b'\x01');o.put(FMT+0x20,b'body\0');o.put(STRING,b'T'*length+b'\0')
        def clock(cpu):cpu.cpu.reg_write(UC_ARM_REG_R1,0);return 0
        o.hooks[0x77b4]=clock;o.hooks[0x312c]=lambda cpu:0
        o.hooks[0x3af4]=lambda cpu:events.append(bytes(cpu.cpu.mem_read(cpu.arg(0),cpu.arg(1))))
        memory,read_cb=memory_for(o)
        o.call(0x8e8c,0,STRING,FMT+0x20,ARGS)
        io=IO(None,WRITE(lambda _,port,data,size:native.append(C.string_at(data,size))),NOW(lambda _:0),COLOR(lambda _:0))
        result=lib.syscon_logger(C.byref(memory),C.byref(io),1,0,STRING,FMT+0x20,ARGS)
        if length<=25:
            assert result==0,(length,result)
            assert native==events
        else:
            # 33 required bytes exceed the actual 32-byte prefix buffer.
            assert result==-2
        if length==25:assert len(events[0])==32 and events[0][-1]==0
