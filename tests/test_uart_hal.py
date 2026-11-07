import ctypes as C
from collections import deque
import random
import struct
import pytest
from test_pwm import Io,READ,WRITE,ASSERT
from uart_hal_oracle import UartHalOracle

class Pair:
    def __init__(self,lib,registers=None):
        self.lib=lib
        self.original=UartHalOracle(registers)
        self.registers=dict(registers or {})
        self.read_scripts={}
        self.trace=[]
        self.board=C.create_string_buffer(232)
        lib.syscon_uart_hal_default_board(self.board)
        assert self.board.raw[:32]==bytes(self.original.cpu.mem_read(self.original.PORTS,32))
        assert self.board.raw[32:]==bytes(self.original.cpu.mem_read(0x2000016c,200))
        self.state=C.create_string_buffer(bytes(self.original.cpu.mem_read(self.original.CONFIG,18)),18)
        self.uart=C.create_string_buffer(156)
        C.memmove(self.uart,bytes(self.original.cpu.mem_read(self.original.RINGS,152)),152)
        C.memmove(C.addressof(self.uart)+152,bytes([self.state.raw[8],self.state.raw[17]]),2)
        def read(_,address):
            if self.read_scripts.get(address): self.registers[address]=self.read_scripts[address].popleft()
            value=self.registers.get(address,0)
            self.trace.append(('read',address,4,value));return value
        def write(_,address,value):
            self.trace.append(('write',address,4,value));self.registers[address]=value
        self.io=Io(None,READ(read),WRITE(write),ASSERT(lambda _,line:self.trace.append(('assert',line))))
        lib.syscon_uart_hal_init.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
        lib.syscon_uart_hal_deinit.argtypes=[C.c_void_p,C.c_void_p,C.c_uint]

    def check(self):
        assert self.trace==self.original.trace
        assert self.registers==self.original.registers
        assert self.state.raw==bytes(self.original.cpu.mem_read(self.original.CONFIG,18))
        assert self.uart.raw[:152]==bytes(self.original.cpu.mem_read(self.original.RINGS,152))
        assert self.uart.raw[152:154]==bytes([self.state.raw[8],self.state.raw[17]])

    def init(self,index,config):
        ptr=0x20000900 if config else 0
        if ptr:self.original.put(ptr,config)
        expected=self.original.invoke(0x8954,index,ptr)
        actual=self.lib.syscon_uart_hal_init(self.state,self.uart,self.board,C.byref(self.io),index,C.c_char_p(config))
        assert C.c_uint32(actual).value==expected
        self.check()

    def deinit(self,index):
        expected=self.original.invoke(0x8b50,index)
        actual=self.lib.syscon_uart_hal_deinit(self.board,C.byref(self.io),index)
        assert C.c_uint32(actual).value==expected
        self.check()


def test_uart_init_deinit_all_baud_boundaries_and_polling_modes(lib):
    rng=random.Random(0x8954)
    for index in (0,1):
        base=0x40108000 if index==0 else 0x40100000
        p=Pair(lib,{base+offset:rng.getrandbits(32) for offset in [0x1100,0x1104,0x1110,0x1114,0x1028]})
        for baud in [0,1,2,3,30,31,32,300,9600,57600,115200,921600,1000000,2000000,2000001,0xffffffff]+[rng.getrandbits(32) for _ in range(100)]:
            for disabled in (0,1,255):
                p.init(index,struct.pack('<HHIB',0x1234,9,baud,disabled))
                p.deinit(index)


def test_uart_partial_config_copy_and_ring_reset(lib):
    rng=random.Random(0x8ace)
    for size in [*range(11),255,65535]:
        for index in (0,1):
            p=Pair(lib)
            config=rng.randbytes(18);rings=rng.randbytes(152)
            C.memmove(p.state,config,18);p.original.put(p.original.CONFIG,config)
            C.memmove(p.uart,rings,152);p.original.put(p.original.RINGS,rings)
            C.memmove(C.addressof(p.uart)+152,bytes([config[8],config[17]]),2)
            p.init(index,struct.pack('<HHIB',0x4321,size,115200,0))


def test_uart_invalid_arguments_and_signed_irq_behavior(lib):
    for index in (2,255,0xffffffff):
        p=Pair(lib)
        p.init(index,struct.pack('<HHIB',1,9,115200,0));p.deinit(index)
    Pair(lib).init(0,None)
    for irq in (-128,-1,0,31,32,127):
        p=Pair(lib)
        C.memmove(C.addressof(p.board)+12,bytes([irq&255]),1)
        p.original.put(p.original.PORTS+12,bytes([irq&255]))
        p.init(0,struct.pack('<HHIB',1,9,115200,0));p.deinit(0)


def test_uart_interrupt_mask_helpers_preserve_other_bits(lib):
    rng=random.Random(0x891c)
    p=Pair(lib,{0x40108000+0x1028:rng.getrandbits(32),0x40100000+0x1028:rng.getrandbits(32)})
    for _ in range(100):
        index=rng.randrange(2)
        name,address=rng.choice([('mask',0x891c),('unmask',0x8938)])
        p.original.invoke(address,index)
        getattr(lib,'syscon_uart_hal_'+name)(p.board,C.byref(p.io),index)
        p.check()


def test_uart_lowlevel_clock_and_format_configuration(lib):
    rng=random.Random(0x95f0)
    base=0x40108000
    p=Pair(lib,{base+0x1100:rng.getrandbits(32),base+0x1104:rng.getrandbits(32)})
    for _ in range(200):
        config=rng.randbytes(10)
        p.original.put(0x20000900,config)
        p.original.invoke(0x95f0,base,0x20000900)
        lib.syscon_uart_hal_configure(C.byref(p.io),base,C.c_char_p(config))
        p.check()
        p.original.invoke(0x9638,base,0x20000900)
        lib.syscon_uart_hal_clock(C.byref(p.io),base,C.c_char_p(config))
        p.check()


def test_uart_preserves_distinct_consecutive_volatile_reads(lib):
    p=Pair(lib)
    address=0x40108000+0x1104
    script=[0xffffffff,0x12345679,0xabcdef00]
    p.read_scripts[address]=deque(script)
    p.original.read_scripts[address]=deque(script)
    p.init(0,struct.pack('<HHIB',1,9,115200,0))
