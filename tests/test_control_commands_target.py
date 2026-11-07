import struct
import pytest
from unicorn import UcError
from control_commands_target_oracle import Pair,build,E,MAPPINGS

@pytest.fixture(scope='module')
def command_elf(tmp_path_factory):return build(tmp_path_factory.mktemp('control-target'))

@pytest.mark.parametrize('entry,args',[ (0x3ef0,None),(0x3f24,None),(0x3fd0,None),
    (0x40fc,None),(0x47b0,None),(0x4420,None),(0x42c8,None)])
def test_simple_commands_use_compiled_variadic_printer_and_exact_dependency_args(command_elf,entry,args):
    p=Pair(command_elf);p.word(E+8,0xdeadbeef);p.run(entry,args)

@pytest.mark.parametrize('entry', [0x3f80,0x47bc,0x40a0])
def test_numeric_commands_use_actual_scan_runtime_including_overflow(command_elf,entry):
    p=Pair(command_elf)
    for args in [b'',b'0',b'1:;',b'-1:;',b'+12xyz',b'  \t42',b'abc',b'+',b'0x10',b'65535',b'65536',
                 b'255',b'256',b'259200',b'259201',b'2147483647',b'2147483648',b'-2147483649',b'9'*100]:
        p.run(entry,args)
    if entry==0x3f80:
        p.results[0x39e8]=1;p.run(entry,b'1')
    if entry==0x40a0:
        for result in (0,1,0x7fffffff,0x80000000,0xffffffff):p.results[0x6650]=result;p.run(entry,None)

@pytest.mark.parametrize('entry,valid',[
    (0x41a4,[b'REBOOT:;',b'POWEROFF:;',b'USER:;',b'BATTERY_LOW:;',b'THERMAL_HIGH:;',b'THERMAL_LOW:;']),
    (0x4258,[b'NORMAL:;',b'FASTBOOT:;',b'FCT:;',b'EDL:;']),
    (0x47fc,[b'ON:;',b'OFF:;']),(0x4850,[b'UP:;',b'DOWN:;',b'POWER:;']),
    (0x48a4,[b'SOFT:;',b'HARD:;']),(0x4970,[b'DETECT:;',b'PASSTHRU:;'])])
def test_exact_strings_invalid_inputs_and_raw_dependency_returns(command_elf,entry,valid):
    p=Pair(command_elf)
    for result in (0,1,0xffffffff):
        for dependency in (0x6428,0x65e4,0x65d0,0x64a0,0x6720):p.results[dependency]=result
        for args in valid+[b'',b'bad',valid[0].lower(),valid[0]+b'x',valid[0][:-1]]:
            p.run(entry,args)
            if entry==0x4850 and args in valid:assert p.calls[0][-1][1][1]==0

def test_pattern_and_rgb_commands_preserve_original_permissive_parsing(command_elf):
    p=Pair(command_elf)
    for result in (0,1,0xffffffff):
        p.results[0x5c68]=result;p.results[0x5c38]=result
        for args in [b'',b'abc',b'0',b'9:0',b'10:0',b'-1:0',b'1:-1',b'1:abc',b'3:2147483648',b'0007:+42:;',b'2:12junk',b'99999999999999999']:
            p.run(0x4320,args)
        for args in [b'1:2:3:4:0:;',b'255:256:999:0:4:;',b'-1:+2:abc:4:3:',b':::::',b'1:2:3:4:5:',
                     b'1234:2:3:4:0:',b'1:2:3:4:0',b'abc',b'%:2:3:4:0:',b'%n:2:3:4:0:']:
            p.run(0x4364,args)
    # Actual callback mutation of the stack token is observed by subsequent
    # source-backed atoi; it is not copied into a host-only parser.
    p.word(E+24,1);p.results[0x5c38]=0;p.run(0x4364,b'1:1:1:1:1:')
    assert p.calls[0][-1][2]==b'\x02'*5

def test_ledstatus_uses_mutable_output_and_preserves_nonboolean_result(command_elf):
    p=Pair(command_elf)
    for result in (0,1,2,0xffffffff):
        p.results[0x5dc8]=result
        for config in (bytes(6),bytes([255,254,253,252,251,250]),bytes([1,2,3,4,5,6])):
            p.rgb=config;p.run(0x42c8)

@pytest.mark.parametrize('entry',[0x48e0,0x49ac])
def test_single_character_flags_keep_original_trailing_text_acceptance(command_elf,entry):
    p=Pair(command_elf)
    for args in (b'0',b'1',b'0anything',b'12345',b'2',b'',b' 1',b'-1'):p.run(entry,args)

def test_direct_modem_payload_preserves_unsigned_length_and_crlf(command_elf):
    p=Pair(command_elf)
    for args in (b'AT:;',b'hello there:;',b':;',b'',b'x',b'\xff\xfe:;'):
        p.run(0x422c,args)
        assert p.calls[0][0][1][1]==(len(args)-2)&0xffffffff
        assert p.calls[0][1][2]==b'\r\n'

def test_error_assert_and_hard_soft_reset_are_terminal_with_exact_side_effect_order(command_elf):
    p=Pair(command_elf)
    for args in (b'1',b'2',b'3',b'-1',b'9999999999999999'):p.run(0x4904,args)
    for args in (b'0',b'abc',b''):p.run(0x4904,args,terminal=True)
    p.run(0x4110,b'bad');p.run(0x4110,b'hard:;')
    for args in (None,b'SOFT:;',b'HARD:;'):
        p.run(0x4110,args,terminal=True)
        expected=[0x37e4,0x5a88,0x77c0,'reset'] if args==b'HARD:;' else [0x77c0,'reset']
        assert [event[0] for event in p.calls[0]]==expected

def test_invalid_printer_pointer_faults_without_being_validated_or_ignored(command_elf):
    p=Pair(command_elf)
    for m,entry in ((p.o,0x3ef0),(p.a,MAPPINGS[0x3ef0])):
        with pytest.raises(UcError):m.call(entry,0,0x30000001)

def test_unmapped_argument_pointer_faults_in_original_runtime_or_direct_byte_read(command_elf):
    for entry in (0x3f80,0x47bc,0x4258,0x4320,0x48e0,0x49ac):
        p=Pair(command_elf)
        for m,fn in ((p.o,entry),(p.a,MAPPINGS[entry])):
            with pytest.raises(UcError):m.call(fn,0x30000000,p.a.symbols['fixture_command_printer'])

def test_raw_rgb_format_callback_can_observe_one_unsupplied_register_argument(command_elf):
    # A narrow executable boundary check, not proof of all undefined varargs.
    # The compiled fixture consumes the actual first va_list word for %d.
    p=Pair(command_elf);p.word(E+28,1);p.run(0x4364,b'%d:2:3:4:0:')

def test_reboot_executes_post_request_barrier_and_wait_loop_if_reset_is_not_applied(command_elf):
    p=Pair(command_elf);p.run(0x4110,b'SOFT:;',terminal=True,spin_reset=True)

def test_uart_parser_dispatches_real_control_handlers_and_source_scan_across_chunks(command_elf):
    p=Pair(command_elf);context=0x20000048;buffer=0x20000300;printer=p.a.symbols['fixture_command_printer']
    p.put(context,struct.pack('<B3xIIBB2xI',0,buffer,0,1,1,printer));p.put(0x200002ee,b'\0')
    chunks=[b'VER',b'SION\nGPIO_READ ',b'65537\nSET_RGB 1:2:3:4:0\n',
            b'560D_ON normal\nKEY_MODE detect\nWAKE_AFTER 12\n',b'560D_DIRECT AT+PING\n',
            b'LEDSTATUS\nREAD_PWR\nDIAG 1junk\nLOG 0\nKEYS up\n',
            b'GPIO_READ junk\nUNKNOWN\nVERSION extra\n']
    for chunk in chunks:
        for pending in p.pending:pending.extend(chunk)
        for m in p.machines:m.put(E,bytes(4))
        for trace in p.calls+p.writes:trace.clear()
        p.o.call(0x49d0,context);p.a.call('syscon_target_protocol_poll',context);p.compare()
        assert p.o.u32(context+8)==p.a.u32(context+8)
