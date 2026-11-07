"""IRQ -> UART -> parser -> real control handler -> formatter -> UART MMIO."""
import ctypes as C
import struct
import pytest
from unicorn import UC_HOOK_MEM_WRITE
from oracle import Oracle
from uart_oracle import Registers,attach_registers,BASES
from test_uart import setup
from test_differential import Parser
from test_control_commands import Io as ControlIO,CALL as ControlCall,PRINT as ControlPrint,LOG as ControlLog
from test_logging import IO as LogIO,WRITE as LogWrite,NOW,COLOR
from test_format import Memory,READ
from test_fault_control import Io as FaultIO,WRITE as FaultWrite

@pytest.mark.parametrize('color',[0,1])
@pytest.mark.parametrize('echo',[0,1])
def test_control_responses_through_real_logging_and_uart(lib,color,echo):
    o=Oracle();registers=Registers();attach_registers(o,registers)
    # Stable post-initialization environment; no physical UART/reset defaults inferred.
    now=12345
    o.put(0x20000678,struct.pack('<Q',now));o.put(0x20000032,bytes([color]))
    o.put(0x2000080c,b'\1')
    o.put(0x20000048,struct.pack('<B3xIIBB2xI',0,0x20000300,0,echo,1,0x8fa1))
    o.hooks[0x8f88]=lambda _:None # Parser diagnostics are a separate documented channel.
    original_stages=[];native_stages=[]
    o.cpu.mem_map(0x400b0000,0x1000)
    def stage(cpu,access,address,size,value,_):
        assert address==0x400b040c and size==4
        original_stages.append((address,value))
    o.cpu.hook_add(UC_HOOK_MEM_WRITE,stage,begin=0x400b0000,end=0x400b0fff)
    _,native,state,uartio=setup(lib)
    faultio=FaultIO();faultio.write=FaultWrite(lambda _,address,value:native_stages.append((address,value)))
    lib.syscon_fault_stage_set.argtypes=[C.c_void_p,C.c_uint32]
    def write(_,port,data,size):
        lib.syscon_fault_stage_set(C.byref(faultio),17)
        lib.syscon_uart_write_buffer(state,port,data,size,C.byref(uartio))
    logio=LogIO(None,LogWrite(write),NOW(lambda _:now),COLOR(lambda _:color))
    regions=[]
    def read(_,address,p):
        for start,data in regions:
            if start<=address<start+len(data):p[0]=data[address-start];return 1
        if address<len(o.image):p[0]=o.image[address];return 1
        return 0
    memory=Memory(READ(read),None)
    lib.syscon_logger.argtypes=[C.POINTER(Memory),C.POINTER(LogIO),C.c_uint8,*([C.c_uint32]*4)]
    def print_message(_,format,values,count):
        regions.clear();regions.append((0x30000000,format+b'\0'));words=[]
        for index in range(count):
            if values[index].is_string:
                address=0x30020000+index*4096;regions.append((address,values[index].string+b'\0'));words.append(address)
            else:words.append(values[index].number)
        regions.append((0x30010000,struct.pack('<'+'I'*len(words),*words)))
        assert lib.syscon_logger(C.byref(memory),C.byref(logio),1,3,0xb849,0x30000000,0x30010000)==0
    errors=[]
    control=ControlIO(None,ControlCall(lambda *args:errors.append(('unexpected dependency',args[1])) or 0),
                      ControlPrint(print_message),ControlLog(lambda *args:errors.append(('unexpected log',))),0)
    parser=Parser();lib.syscon_parser_init(C.byref(parser),1,echo)
    ECHO=C.CFUNCTYPE(None,C.c_void_p,C.c_uint8)
    echo_cb=ECHO(lambda _,byte:lib.syscon_uart_write(state,0,byte,C.byref(uartio)))
    lib.syscon_control_feed.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
    stream=b'Version\r\nHELP\nVERSION unexpected\nwhat\nVERSIONjunk\n'
    for offset in range(0,len(stream),17):
        for byte in stream[offset:offset+17]:
            for r in [registers,native]:r.values[BASES[0]+0x1020]=11;r.values[BASES[0]+0x1124]=byte
            o.call(0x8d70,BASES[0]);lib.syscon_uart_irq(state,BASES[0],C.byref(uartio))
        o.call(0x49d0,0x20000048,count=3000000)
        while lib.syscon_uart_available(state,0,C.byref(uartio)):
            byte=lib.syscon_uart_read(state,0,C.byref(uartio))
            assert lib.syscon_control_feed(C.byref(control),C.byref(parser),bytes([byte]),1,None,None,echo_cb,None)==0
        assert not errors
        tx=lambda r:[event for event in r.trace if event[:2]==('write',BASES[0]+0x1120)]
        assert tx(native)==tx(registers)
        assert native_stages==original_stages
        assert state.raw[:152]==bytes(o.cpu.mem_read(0x20000774,152))
        assert bytes(parser.storage[1:])==bytes(o.cpu.mem_read(0x20000300,128))
