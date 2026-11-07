import ctypes as C
import struct
from unicorn.arm_const import UC_ARM_REG_R1
from oracle import Oracle
from test_format import READ,Memory

WRITE=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint32)
NOW=C.CFUNCTYPE(C.c_uint64,C.c_void_p)
COLOR=C.CFUNCTYPE(C.c_int,C.c_void_p)
class IO(C.Structure):_fields_=[('ctx',C.c_void_p),('write',WRITE),('now',NOW),('color',COLOR)]

def memory_for(o):
    ram=bytes(o.cpu.mem_read(0x20000000,4096))
    def read(_,address,p):
        if address<len(o.image):p[0]=o.image[address];return 1
        if 0x20000000<=address<0x20001000:p[0]=ram[address-0x20000000];return 1
        return 0
    cb=READ(read);return Memory(cb,None),cb


def test_sg560d_formatted_uart_truncation_and_arm_alignment(lib):
    lib.syscon_sg560d_printf.argtypes=[C.POINTER(Memory),C.POINTER(IO),C.c_uint32,C.c_uint32]
    for format in [b'',b'hello',b'%u %x %lld',b'%cafter',b'x'*127,b'x'*128,b'x'*200,b'%03d %hhd %p']:
        for first in [0,255,0xffffffff]:
            o=Oracle();events=[];native=[]
            o.put(0x20000800,format+b'\0')
            words=[first,0x12345678,0x7fffffff,0x89abcdef,1,2,3]
            # The real variadic wrapper starts saved arguments at SP-12 (alignment4).
            o.put(0x20000904,struct.pack('<7I',*words))
            memory,read_cb=memory_for(o)
            o.hooks[0x8c8c]=lambda cpu:events.append((cpu.arg(0),bytes(cpu.cpu.mem_read(cpu.arg(1),cpu.arg(2)))))
            o.call(0x5edc,0x20000800,*words)
            write=WRITE(lambda _,port,data,size:native.append((port,C.string_at(data,size))))
            io=IO(None,write,NOW(lambda _:0),COLOR(lambda _:0))
            assert lib.syscon_sg560d_printf(C.byref(memory),C.byref(io),0x20000800,0x20000904)==0
            assert native==events,(format,first,native,events)


def test_logger_prefix_colors_lengths_and_binary_output(lib):
    lib.syscon_logger.argtypes=[C.POINTER(Memory),C.POINTER(IO),C.c_uint8,*([C.c_uint32]*4)]
    for format in [b'',b'a',b'X'*31,b'X'*32,b'X'*255,b'X'*256,b'X'*300,b'%c%u %lld %p']:
        for level in [0,1,2,3,4,5]:
            for colors in [[0,0],[1,1],[0,1],[1,0]]:
                o=Oracle();events=[];native=[];oc=colors[:];nc=colors[:]
                o.put(0x2000080c,b'\x01')
                o.put(0x20000820,format+b'\0');o.put(0x20000960,b'TEST\0')
                o.put(0x20000980,struct.pack('<8I',0,0xffffffff,0x12345678,0x7fffffff,0,0,0,0))
                now=0x100000000+12345
                def clock(cpu):events.append(('clock',now));cpu.cpu.reg_write(UC_ARM_REG_R1,now>>32);return now&0xffffffff
                def color(cpu):v=oc.pop(0);events.append(('color',v));return v
                o.hooks[0x77b4]=clock;o.hooks[0x312c]=color
                o.hooks[0x3af4]=lambda cpu:events.append(('write',0,bytes(cpu.cpu.mem_read(cpu.arg(0),cpu.arg(1)))))
                memory,read_cb=memory_for(o)
                o.call(0x8e8c,level,0x20000960,0x20000820,0x20000980)
                write=WRITE(lambda _,port,data,size:native.append(('write',port,C.string_at(data,size))))
                def native_clock(_):native.append(('clock',now));return now
                def native_color(_):v=nc.pop(0);native.append(('color',v));return v
                io=IO(None,write,NOW(native_clock),COLOR(native_color))
                assert lib.syscon_logger(C.byref(memory),C.byref(io),1,level,0x20000960,0x20000820,0x20000980)==0
                assert native==events,(format,level,colors,native,events)


def test_disabled_logger_has_no_dependency_calls(lib):
    o=Oracle();o.put(0x2000080c,b'\0');events=[]
    o.hooks[0x312c]=lambda cpu:events.append('color')
    o.hooks[0x77b4]=lambda cpu:events.append('time')
    o.hooks[0x3af4]=lambda cpu:events.append('write')
    o.call(0x8e8c,1,0,0,0)
    memory,read_cb=memory_for(o)
    io=IO(None,WRITE(lambda *args:events.append('write')),NOW(lambda _:events.append('time') or 0),COLOR(lambda _:events.append('color') or 0))
    assert lib.syscon_logger(C.byref(memory),C.byref(io),0,1,0,0,0)==0
    assert not events
