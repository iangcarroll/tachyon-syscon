import ctypes as C
import random
import struct
from oracle import Oracle

READ=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.POINTER(C.c_uint8))
class Memory(C.Structure):_fields_=[('read',READ),('ctx',C.c_void_p)]
class Result(C.Structure):_fields_=[('length',C.c_uint32),('next_argument',C.c_uint32),('complete',C.c_int)]

def run_case(lib,format,args,cap=128,alignment=0,no_output=False):
    o=Oracle();fmt=0x20000800;arg=0x20000900+alignment;dest=0x20000b00
    o.put(fmt,format+b'\0');o.put(arg,args.ljust(256,b'\0'))
    o.put(0x20000a20,b'Example string!\0');o.put(0x20000a40,b'\0')
    initial=bytes([0xa5])*256;o.put(dest,initial)
    ram=bytes(o.cpu.mem_read(0x20000000,4096))
    def read(_,address,p):
        if address< len(o.image):p[0]=o.image[address];return 1
        if 0x20000000<=address<0x20001000:p[0]=ram[address-0x20000000];return 1
        return 0
    cb=READ(read);memory=Memory(cb,None);buf=C.create_string_buffer(initial,256)
    lib.syscon_vformat.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.POINTER(Memory)]
    lib.syscon_vformat.restype=Result
    expected=o.call(0x92ac,0 if no_output else dest,cap,fmt,arg)
    result=lib.syscon_vformat(None if no_output else buf,cap,fmt,arg,C.byref(memory))
    assert result.complete
    assert result.length==expected,(format,args,cap,result.length,expected)
    assert buf.raw==bytes(o.cpu.mem_read(dest,256)),(format,args,cap,buf.raw,bytes(o.cpu.mem_read(dest,256)))


def test_formatter_integer_flags_lengths_and_target_varargs_alignment(lib):
    rng=random.Random(0x9038)
    for length in [b'',b'h',b'hh',b'l',b'll',b'j',b'z',b't']:
        for spec in [b'd',b'i',b'u',b'o',b'x',b'X',b'p',b'c',b'%']:
            for flags in [b'',b'+',b' ',b'#',b'#+ ',b' +#']:
                args=struct.pack('<8I',*[rng.getrandbits(32) for _ in range(8)])
                run_case(lib,b'a%'+flags+length+spec+b'/%u!',args,cap=rng.choice([0,1,2,10,64,128]),alignment=rng.choice([0,4]))


def test_formatter_unsupported_syntax_strings_and_truncation(lib):
    args=struct.pack('<12I',*([0x20000a20,0x20000a40]*6))
    formats=[b'',b'%',b'%#',b'%03d %.2f %f %e %-s',b'%s/%ls/%hhs/%zs',b'%p %p %p',b'%% %q %a %n',b'\xff%+d\x80',b'%#+ +##llx']
    for f in formats:
        for cap in [0,1,2,5,16,127,128]:
            for no_output in [False,True]:run_case(lib,f,args,cap,no_output=no_output)


def test_formatter_integer_extremes(lib):
    for value in [0,1,0x7fffffff,0x80000000,0xffffffff,0x7fffffffffffffff,0x8000000000000000,0xffffffffffffffff]:
        args=struct.pack('<4Q',value,value,value,value)
        for f in [b'%lld',b'%#llo',b'%#llx',b'%hhd',b'%hd',b'%p']:
            run_case(lib,f,args)
