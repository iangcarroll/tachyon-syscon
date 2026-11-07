import ctypes as C
import random
import struct
from uart_oracle import UartOracle,Registers,BASES

READ=C.CFUNCTYPE(C.c_uint32,C.c_void_p,C.c_uint32)
WRITE=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32,C.c_uint32)
class IO(C.Structure):
    _fields_=[('read',READ),('write',WRITE),('ctx',C.c_void_p)]

def setup(lib):
    original=UartOracle();native=Registers();state=C.create_string_buffer(original.state(),156)
    read=READ(lambda _,a:native.read(a));write=WRITE(lambda _,a,v:native.write(a,v))
    io=IO(read,write,None)
    for name in ['available','read']:
        getattr(lib,'syscon_uart_'+name).argtypes=[C.c_void_p,C.c_uint,C.POINTER(IO)]
    lib.syscon_uart_irq.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(IO)]
    lib.syscon_uart_write.argtypes=[C.c_void_p,C.c_uint,C.c_uint32,C.POINTER(IO)]
    lib.syscon_uart_write_buffer.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_size_t,C.POINTER(IO)]
    return original,native,state,io

def test_uart_ring_interrupts_overflow_disable_and_wrap(lib):
    o,native,state,io=setup(lib);rng=random.Random(0x8d70)
    for step in range(2500):
        port=rng.randrange(2);base=BASES[port]
        operation=rng.choice(['irq']*4+['read','available','mode'])
        o.registers.trace.clear();native.trace.clear()
        if operation=='mode':
            value=rng.choice([0,0,1,255]);state[152+port]=value
            o.put(0x2000076a+port*9,bytes([value]))
        elif operation=='irq':
            reason=rng.choice([11,11,11,0,10,267]);value=rng.getrandbits(32)
            for r in [o.registers,native]:r.values[base+0x1020]=reason;r.values[base+0x1124]=value
            o.call(0x8d70,base);lib.syscon_uart_irq(state,base,C.byref(io))
        else:
            address=0x8de4 if operation=='read' else 0x8cf0
            expected=C.c_int32(o.call(address,port)).value
            assert getattr(lib,'syscon_uart_'+operation)(state,port,C.byref(io))==expected
        assert state.raw==o.state(),(step,operation)
        assert native.trace==o.registers.trace,(step,operation)
        assert native.values==o.registers.values

def test_uart_transmit_busy_fifo_and_disabled_ports(lib):
    o,native,state,io=setup(lib);rng=random.Random(0x8c34)
    for step in range(200):
        port=rng.randrange(2);disabled=rng.choice([0,0,1,255])
        state[152+port]=disabled;o.put(0x2000076a+port*9,bytes([disabled]))
        for r in [o.registers,native]: r.trace.clear();r.busy=step%7
        if step%2:
            value=rng.getrandbits(32)
            assert o.call(0x8c34,port,value)==lib.syscon_uart_write(state,port,value,C.byref(io))
        else:
            data=rng.randbytes(rng.randrange(100));o.put(0x20000900,data)
            assert o.call(0x8c8c,port,0x20000900,len(data))==lib.syscon_uart_write_buffer(state,port,C.c_char_p(data),len(data),C.byref(io))
        assert native.trace==o.registers.trace
        assert native.values==o.registers.values


def test_uart_interrupt_to_parser_and_echo_pipeline(lib):
    from oracle import ProtocolOracle
    from uart_oracle import attach_registers
    from test_differential import Parser,DISPATCH,PRINT,ECHO
    _,native,state,io=setup(lib)
    o=ProtocolOracle(echo=True)
    for address in [0x8cf0,0x8de4,0x8c34]: del o.hooks[address]
    original_registers=Registers();attach_registers(o,original_registers)
    parser=Parser();lib.syscon_parser_init(C.byref(parser),1,1)
    events=[]
    def dispatch(_,address,arg):
        events.append(('dispatch',address,None if arg is None else arg.decode('latin1')))
        return 1
    emit=PRINT(lambda _,text:events.append(('print',text.decode('latin1'))))
    dispatch_cb=DISPATCH(dispatch)
    echo=ECHO(lambda _,byte:lib.syscon_uart_write(state,0,byte,C.byref(io)))
    chunks=[b'VERSION\r\n',b'CONFIG_SET sys.auto_boot true\n',b'X'*90,
            b'\r\nHELP\n',b'\0\t\x7fCONFIG_GET sys.auto_boot\n',b';\n']
    base=BASES[0]
    for chunk in chunks:
        for byte in chunk:
            for r in [native,original_registers]:
                r.values[base+0x1020]=11;r.values[base+0x1124]=byte
            o.call(0x8d70,base);lib.syscon_uart_irq(state,base,C.byref(io))
        o.call(0x49d0,o.CONTEXT)
        while lib.syscon_uart_available(state,0,C.byref(io)):
            byte=lib.syscon_uart_read(state,0,C.byref(io))
            lib.syscon_parser_feed(C.byref(parser),bytes([byte]),C.c_size_t(1),dispatch_cb,emit,echo,None)
        assert events==o.events
        assert bytes(parser.storage[1:])==bytes(o.cpu.mem_read(o.BUFFER,128))
        assert parser.used==o.u32(o.CONTEXT+8)
        assert state.raw[:152]==bytes(o.cpu.mem_read(0x20000774,152))
        transmitted=lambda r:[t for t in r.trace if t[:2]==('write',base+0x1120)]
        assert transmitted(native)==transmitted(original_registers)
