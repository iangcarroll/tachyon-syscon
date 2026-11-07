import ctypes as C
import random
import pytest
from control_protocol_oracle import ControlOracle,ControlDependencies
from inventory import command_table,load_image

class FormatArg(C.Structure):
    _fields_=[('is_string',C.c_uint32),('number',C.c_uint32),('string',C.c_char_p)]
CALL=C.CFUNCTYPE(C.c_int32,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32,C.c_void_p,C.c_uint32)
PRINT=C.CFUNCTYPE(None,C.c_void_p,C.c_char_p,C.POINTER(FormatArg),C.c_uint)
LOG=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_char_p,C.c_char_p,C.POINTER(FormatArg),C.c_uint)
DISPATCH=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint32,C.c_char_p)
RAWPRINT=C.CFUNCTYPE(None,C.c_void_p,C.c_char_p)
ECHO=C.CFUNCTYPE(None,C.c_void_p,C.c_uint8)

class Io(C.Structure):
    _fields_=[('context',C.c_void_p),('call',CALL),('print',PRINT),('log',LOG),('debug',C.c_uint8)]

class Pair:
    def __init__(self,lib,results=None):
        self.lib=lib
        self.native=ControlDependencies(results)
        self.original=ControlDependencies(results)
        self.oracle=ControlOracle(self.original)
        def call(_,addr,a,b,data,size):
            incoming=C.string_at(data,size) if data and addr in (0x5c38,0x74e8,0x2678) else None
            result=self.native.call(addr,a,b,incoming,size)
            if addr in self.native.outputs: C.memmove(data,self.native.outputs[addr],size)
            return result
        def args(values,count):
            return tuple(values[i].string.decode('latin1') if values[i].is_string else values[i].number for i in range(count))
        self.io=Io(None,CALL(call),
            PRINT(lambda _,fmt,values,count:self.native.events.append(('print',fmt.decode('latin1'),args(values,count)))),
            LOG(lambda _,level,tag,fmt,values,count:self.native.events.append(('log',level,tag.decode(),fmt.decode('latin1'),args(values,count)))),0)
        lib.syscon_control_command.argtypes=[C.c_void_p,C.c_uint32,C.c_char_p]
        lib.syscon_control_command.restype=C.c_int32
        self.parser=C.create_string_buffer(140)
        lib.syscon_parser_init(self.parser,1,0)
        self.dispatch=DISPATCH(lambda _,handler,arg:lib.syscon_control_command(C.byref(self.io),handler,arg))
        self.rawprint=RAWPRINT(lambda _,text:self.native.events.append(('print',text.decode('latin1'),())))
        self.echo=ECHO(lambda _,byte:None)
        lib.syscon_control_feed.argtypes=[C.c_void_p,C.c_void_p,C.c_void_p,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
        lib.syscon_control_feed.restype=C.c_int32

    def check(self):
        assert self.native.events==self.original.events
        assert self.io.debug==self.oracle.cpu.mem_read(self.oracle.DEBUG,1)[0]

    def invoke(self,handler,args):
        expected=self.oracle.invoke(handler,args)
        actual=self.lib.syscon_control_command(C.byref(self.io),handler,args)
        assert C.c_uint32(actual).value==expected,(hex(handler),args,actual,expected)
        self.check()

    def feed(self,data):
        returned=self.oracle.feed(data)
        result=self.lib.syscon_control_feed(C.byref(self.io),self.parser,C.c_char_p(data),len(data),None,None,None,None)
        assert result==(0 if returned else -2147483648)
        self.check()


CASES={
0x3ef0:[None],0x3f24:[None],0x3f80:[b'0:;',b'15:;',b'-1:;',b'65536:;',b'no:;'],
0x3fd0:[None],0x40a0:[None,b'0:;',b'259200:;',b'259201:;',b'-1:;',b'+20tail:;'],
0x40fc:[None],0x4110:[None,b'SOFT:;',b'HARD:;',b'hard:;',b'OTHER:;'],
0x41a4:[x+b':;' for x in [b'REBOOT',b'POWEROFF',b'USER',b'BATTERY_LOW',b'THERMAL_HIGH',b'THERMAL_LOW',b'UNKNOWN']],
0x422c:[b'AT+X=1:;',b'RESET:;',b':;'],
0x4258:[x+b':;' for x in [b'NORMAL',b'FASTBOOT',b'FCT',b'EDL',b'OTHER']],
0x42c8:[None],0x4320:[b'0:;',b'9:40:;',b'10:;',b'-1:;',b'abc:;',b'1:-1:;',b'3:abc:;'],
0x4364:[b'1:2:3:50:1:;',b'255:256:999:-1:4:;',b'abc::0:90:5:;',b'1:2:3:4:260:;',b'1:2:3:4:-1:;',b'1000:2:3:4:0:;',b'1:2:3:4',b'%s:2:3:4:1:;'],
0x4420:[None],0x47b0:[None],0x47bc:[b'0:;',b'24:;',b'65536:;',b'-1:;',b'no:;'],
0x47fc:[b'ON:;',b'OFF:;',b'on:;',b'UNKNOWN:;'],
0x4850:[b'UP:;',b'DOWN:;',b'POWER:;',b'OTHER:;'],
0x48a4:[b'SOFT:;',b'HARD:;',b'OTHER:;'],0x48e0:[b'0:;',b'1:;',b'1junk:;',b'10:;',b'2:;'],
0x4904:[b'0:;',b'1:;',b'2:;',b'3:;',b'abc:;',b'-1:;'],
0x4970:[b'DETECT:;',b'PASSTHRU:;',b'OTHER:;'],0x49ac:[b'0:;',b'1:;',b'100:;',b'x:;']}

@pytest.mark.parametrize('dependency_result',[-1,0,1,5])
def test_control_handlers_against_original_for_dependency_results(lib,dependency_result):
    addresses=[0x5358,0x6650,0x74f8,0x37e4,0x5a88,0x6428,0x65e4,0x65d0,0x64a0,0x5274,
               0x65f0,0x77c0,0x55dc,0x4c50,0x7468,0x6720,0x347c,0x8fc0,0x591c,0x80f8,0x39e8,0x5dc8,0x5c38,0x5c68,0x74e8]
    p=Pair(lib,{address:dependency_result for address in addresses})
    for handler,cases in CASES.items():
        for args in cases: p.invoke(handler,args)


def test_control_commands_through_full_parser_chunking_and_aliases(lib):
    rng=random.Random(0x49d0)
    p=Pair(lib)
    table=command_table(load_image())
    for entry in table:
        handler=entry['handler']
        if handler not in CASES: continue
        for args in CASES[handler]:
            if handler==0x4110 and args in (None,b'SOFT:;',b'HARD:;'): continue
            if handler==0x4904 and args in (b'0:;',b'abc:;'): continue
            # The raw-format testcase is safe at the documented format-call boundary.
            line=entry['name'].lower().encode()+ (b':'+args if args is not None else b'')+b'\r\n'
            if handler==0x4110 and args==b'hard:;': continue # parser uppercases -> reset
            for offset in range(0,len(line),3): p.feed(line[offset:offset+3])
    for _ in range(60):
        line=rng.choice([b'LOG 1junk\n',b'DIAG 0tail\n',b'power normal\n',b'gpio_read -1\n',b'VERSIONjunk\n',b'WAKE_AFTER\n'])
        p.feed(line)


def test_decimal_boundaries_and_trailing_input(lib):
    p=Pair(lib)
    for token in [b'',b'+',b'-',b'0x10',b'0123',b'123junk',b'-2147483648',b'-2147483649',
                  b'2147483647',b'2147483648',b'4294967295',b'4294967296',b'9'*60,b'-'+b'9'*60,b'\t+2']:
        for handler in (0x3f80,0x47bc,0x40a0,0x4320,0x4904):
            p.invoke(handler,token+b':;')


def test_random_set_rgb_and_pattern_parser_inputs(lib):
    rng=random.Random(0x4364)
    p=Pair(lib)
    tokens=[b'',b'0',b'1',b'-1',b'255',b'256',b'260',b'999',b'abc',b'+2',b' 1',b'%d']
    for _ in range(250):
        args=b':'.join(rng.choice(tokens) for _ in range(5))+b':;'
        p.invoke(0x4364,args)
    for _ in range(200):
        p.invoke(0x4320,rng.choice(tokens)+b':'+rng.choice(tokens)+b':;')


@pytest.mark.parametrize('line',[b'REBOOT\n',b'MCU_REBOOT HARD\n',b'reboot soft\n',b'ERROR 0\n',b'error abc\n'])
def test_control_terminal_commands_stop_pipeline_before_pass_and_next_command(lib,line):
    p=Pair(lib)
    p.feed(line+b'VERSION\n')
    assert not any(e[0]=='print' and e[1] in ('PASS','Version=%s') for e in p.native.events)


def test_control_unimplemented_dependency_dispatch_fails_closed(lib):
    p=Pair(lib)
    data=b'CONFIG_INTERNAL\nVERSION\n'
    result=lib.syscon_control_feed(C.byref(p.io),p.parser,C.c_char_p(data),len(data),None,None,None,None)
    assert result==-2147483647
    assert p.native.events==[]


def test_control_parser_forwards_config_handlers_to_explicit_fallback(lib):
    p=Pair(lib)
    calls=[]
    callback=DISPATCH(lambda _,handler,args:(calls.append((handler,args)) or 0))
    data=b'CONFIG_INTERNAL\nVERSION\n'
    result=lib.syscon_control_feed(C.byref(p.io),p.parser,C.c_char_p(data),len(data),callback,None,None,None)
    assert result==0
    assert calls==[(0x3fdc,None)]
    assert p.native.events==[('print','FAIL',()),('print','Version=%s',('1.0.52',)),('print','PASS',())]
