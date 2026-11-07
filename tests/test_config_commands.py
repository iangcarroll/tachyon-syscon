"""End-to-end UART configuration flows against original CPU execution."""
import ctypes as C
import random
import pytest
from config_protocol_oracle import ConfigProtocolOracle
from test_config_updates import NativeStore, Store, image
from test_differential import Parser, PRINT, ECHO, DISPATCH

class Context(C.Structure):
    _fields_=[('config',C.POINTER(Store)),('identity',C.POINTER(Store)),
              ('runtime',C.c_uint8*22),('print',PRINT),('print_context',C.c_void_p)]

class Pipeline:
    def __init__(self,lib,config,identity,echo=False,fail=None):
        self.lib=lib
        self.oracle=ConfigProtocolOracle(config,identity,echo,fail)
        self.config=NativeStore(lib,config)
        self.identity=NativeStore(lib,identity,count=16)
        self.events=[];self.flash_events=[]
        # Native and ARM stores share one controller's failure counter.
        counts={}
        for native,base in [(self.config,0),(self.identity,-1024)]:
            original=native.flash.operation
            def operation(kind,off,data=b'',original=original,native=native,base=base):
                counts[kind]=counts.get(kind,0)+1
                # Configure this per-store model to fail at the shared occurrence.
                native.flash.fail=(kind,native.flash.counts.get(kind,0)+1) if fail==(kind,counts[kind]) else None
                result=original(kind,off,data)
                self.flash_events.append((kind,off+base,bytes(data),result))
                return result
            native.flash.operation=operation
        self.print_cb=PRINT(lambda _,text:self.events.append(('print',text.decode('latin1'))))
        self.echo_cb=ECHO(lambda _,b:self.events.append(('echo',b)))
        self.context=Context(C.pointer(self.config.store),C.pointer(self.identity.store),print=self.print_cb)
        self.context.runtime[:]=self.oracle.cpu.mem_read(0x20000030,22)
        self.parser=Parser()
        self.lib.syscon_parser_init(C.byref(self.parser),1,int(echo))
        self.lib.syscon_config_dispatch.argtypes=[C.c_void_p,C.c_uint32,C.c_char_p]
        self.dispatch_cb=DISPATCH(lambda _,handler,arg:self.lib.syscon_config_dispatch(C.byref(self.context),handler,arg))

    def feed(self,data,chunk_size=7):
        for i in range(0,len(data),chunk_size):
            chunk=data[i:i+chunk_size]
            self.oracle.feed(chunk)
            self.lib.syscon_parser_feed(C.byref(self.parser),chunk,C.c_size_t(len(chunk)),self.dispatch_cb,self.print_cb,self.echo_cb,None)
            assert self.events==self.oracle.events,chunk
            assert self.config.contents()==bytes(self.oracle.cpu.mem_read(0xfc00,1024)),chunk
            assert self.identity.contents()==bytes(self.oracle.cpu.mem_read(0xf800,1024)),chunk
            assert self.flash_events==self.oracle.flash.events,chunk
            assert bytes(self.context.runtime)==bytes(self.oracle.cpu.mem_read(0x20000030,22)),chunk


@pytest.mark.parametrize('echo',[False,True])
def test_uart_persistent_config_flows(lib,echo):
    initial=image(lib,[(0,b'confVersion',b'1')])
    p=Pipeline(lib,initial,initial,echo)
    p.feed(b'CONFIG_INTERNAL\n')
    p.feed(b'CONFIG_ID_SET hw_revision 1.3\r\nCONFIG_ID_GET hw_revision\n')
    p.feed(b'CONFIG_SET sys.auto_boot true\nCONFIG_GET sys.auto_boot\nCONFIG_SET sys.auto_boot true\n')
    p.feed(b'CONFIG_SET sys.edl_timer 7\nCONFIG_SET sys.shutdown_timer 999999999999999999999999\n')
    p.feed(b'CONFIG_INTERNAL\n')
    for i in range(28):p.feed(f'config_set:key{i%3}:value{i}:;\n'.encode())
    p.feed(b'CONFIG_DUMP\nCONFIG_ID_DUMP\nCONFIG_FIND 0\nCONFIG_FIND 4junk\nCONFIG_FIND not-a-number\n')
    p.feed(b'CONFIG_ID_FIND -1\nCONFIG_ID_FIND 0\nCONFIG_ID_FIND 1\nCONFIG_ID_FIND 99999999999999999999\n')
    p.feed(b'CONFIG_ERASE wrong\nCONFIG_ID_ERASE wrong\nCONFIG_ERASE particle\nCONFIG_ID_ERASE particle\n')
    p.feed(b'CONFIG_ID_ERASE B23000\n')
    p.feed(b'CONFIG_INTERNAL\n')
    p.feed(b'CONFIG_DUMP\nCONFIG_ID_DUMP\nCONFIG_GET missing\n')


def test_uart_malformed_arguments_and_legacy_corruption(lib):
    initial=bytearray(image(lib,[(0,b'confVersion',b'1'),(2,b'a',b'good'),(6,b'a',b'bad')]))
    initial[6*64+63]^=1
    p=Pipeline(lib,initial,initial)
    p.feed(b'CONFIG_GET a\nCONFIG_FIND 6\nCONFIG_DUMP\nCONFIG_ID_DUMP\n')
    for command in [b'CONFIG_SET',b'CONFIG_ID_SET',b'CONFIG_GET',b'CONFIG_ID_GET',b'CONFIG_FIND',b'CONFIG_ID_FIND',b'CONFIG_ERASE',b'CONFIG_ID_ERASE']:
        for suffix in [b'',b':;',b'::;',b':a:;',b':a::;',b':a:b:extra;',b':'+b'x'*31+b':v:;',b':'+b'x'*32+b':v:;',b': a:b:;',b':a:v;trailer']:
            p.feed(command+suffix+b'\n')


@pytest.mark.parametrize('failure',[('erase',1),('program',1),('program',5),('blank',1)])
def test_uart_config_flash_failure_responses(lib,failure):
    initial=image(lib,[(0,b'confVersion',b'1')])
    p=Pipeline(lib,initial,initial,fail=failure)
    p.feed(b'CONFIG_SET some_key first\nCONFIG_GET some_key\nCONFIG_DUMP\n')
    # The injected erase error is non-resetting; failed erase reports password text.
    if failure[0]=='erase':p.feed(b'CONFIG_ERASE particle\nCONFIG_DUMP\n')
