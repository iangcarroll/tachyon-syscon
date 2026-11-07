"""Differential tests execute the pinned machine code, not duplicate expectations.

Protocol tests cover UART ingestion through dispatch and PASS/FAIL framing;
handler bodies and physical peripherals are explicitly outside that test boundary.
"""
import ctypes as C
import random
import struct
import pytest
from oracle import Oracle, ProtocolOracle
from inventory import command_table, load_image


class Parser(C.Structure):
    _fields_ = [('storage', C.c_uint8 * 129), ('used', C.c_uint32),
                ('enabled', C.c_uint8), ('echo', C.c_uint8)]


DISPATCH = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_uint32, C.c_char_p)
PRINT = C.CFUNCTYPE(None, C.c_void_p, C.c_char_p)
ECHO = C.CFUNCTYPE(None, C.c_void_p, C.c_uint8)


def reconstructed_events(lib, chunks, result=1, echo=False, enabled=True):
    events = []
    p = Parser()
    lib.syscon_parser_init(C.byref(p), int(enabled), int(echo))
    def dispatch(_, address, arg):
        events.append(('dispatch', address, None if arg is None else arg.decode('latin1')))
        return result
    def emit(_, text):
        events.append(('print', text.decode('latin1')))
    def echo_byte(_, b):
        events.append(('echo', b))
    dispatch_cb, print_cb, echo_cb = DISPATCH(dispatch), PRINT(emit), ECHO(echo_byte)
    for chunk in chunks:
        lib.syscon_parser_feed(C.byref(p), chunk, C.c_size_t(len(chunk)),
                                dispatch_cb, print_cb, echo_cb, None)
    return events, p


@pytest.mark.parametrize('address,name', [(0x282c, 'syscon_checksum31'),
                                         (0x27dc, 'syscon_field_readable'),
                                         (0x2810, 'syscon_field_writable')])
def test_fields_original_machine_code(lib, address, name):
    o = Oracle()
    rng = random.Random(0x1306)
    cases = [bytes([c])*n + b'\0' + b'\xff'*32 for c in range(256) for n in [1, 30, 31]]
    cases += [rng.randbytes(31) + b'\0' for _ in range(256)]
    cases += [b'sys.auto_boot\0', b'1234567890\0', b'foo;bar\0', b'\0']
    for data in cases:
        data = data.ljust(64, b'\xff')
        o.put(0x20000900, data)
        expected = o.call(address, 0x20000900)
        actual = getattr(lib, name)(C.c_char_p(data))
        assert actual == expected, (name, data)


def test_slot_encoding_and_corruption(lib):
    o = Oracle()
    o.hooks[0x8f88] = lambda _: None
    # Explicit flash-controller model: only blank-check and double-word programming.
    o.hooks[0x7b44] = lambda _: None
    o.hooks[0x7b60] = lambda _: 3
    def program_doubleword(cpu):
        cpu.put(cpu.arg(1), cpu.cpu.mem_read(cpu.arg(2), 8))
        return 3
    o.hooks[0x7b10] = program_doubleword
    rng = random.Random(73)
    for _ in range(120):
        alphabet = b'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.'
        key = bytes(rng.choice(alphabet) for _ in range(rng.randrange(1,31)))
        value = bytes(rng.choice(alphabet) for _ in range(rng.randrange(1,31)))
        slot = C.create_string_buffer(64)
        assert lib.syscon_slot_encode(slot, key, value) == 1
        o.put(0x20000900, key+b'\0')
        o.put(0x20000940, value+b'\0')
        assert o.call(0x28d4, 0xfc00, 0x20000900, 0x20000940) == 1
        assert slot.raw == bytes(o.cpu.mem_read(0xfc00,64))
        # All 64 byte positions, including both checksums, get a fault injection.
        for j in range(64):
            mutated = bytearray(slot.raw)
            mutated[j] ^= 1 << rng.randrange(8)
            o.put(0x20000980, mutated)
            expected = o.call(0x2840, 0x20000980)
            assert lib.syscon_slot_valid(C.c_char_p(bytes(mutated))) == expected


def test_latest_matching_slot_preserves_original_corruption_behavior(lib):
    o = Oracle()
    o.hooks[0x8f88] = lambda _: None
    o.hooks[0x79d0] = lambda _: None
    slots = bytearray(b'\xff' * 960)
    for index, value in [(1,b'false'),(5,b'true')]:
        slot=C.create_string_buffer(64)
        assert lib.syscon_slot_encode(slot,b'sys.auto_boot',value)
        slots[index*64:(index+1)*64]=slot.raw
    slots[5*64+63] ^= 1  # Newest matching slot is corrupt but still selected by original.
    o.put(0xfc00, slots)
    o.put(0x20000900, b'sys.auto_boot\0')
    assert o.call(0x29a0, 0xfc00, 960, 0x20000900, 1, 0x20000940) == 1
    expected=(o.u32(0x20000940)-0xfc00)//64
    assert lib.syscon_find_legacy(C.c_char_p(bytes(slots)),15,b'sys.auto_boot') == expected


@pytest.mark.parametrize('result', [0,1,-1])
@pytest.mark.parametrize('echo', [False,True])
def test_all_commands_dispatch_with_chunked_uart(lib, result, echo):
    stream=bytearray()
    for cmd in command_table(load_image()):
        for suffix in [b'',b':;',b' x:;',b':mixedCase:42:;',b'JUNK',b'::;',b' :;']:
            stream += cmd['name'].swapcase().encode()+suffix+b'\r\n'
    stream += b'what\n;\n\0\x01\x09\x7f\xffVERSION\n'
    chunks=[bytes(stream[i:i+7]) for i in range(0,len(stream),7)]
    o=ProtocolOracle(result,echo)
    for chunk in chunks: o.feed(chunk)
    actual,p=reconstructed_events(lib,chunks,result,echo)
    assert actual == o.events
    assert p.used == o.u32(o.CONTEXT+8)


def test_stream_overflows_and_noise(lib):
    rng=random.Random(0x49d0)
    chunks=[b'VERSION\n', b'A'*125+b'Z', b'\n', b';\n', b' '*124+b'\n']
    chunks += [rng.randbytes(rng.randrange(1,200))+b'\r\n' for _ in range(80)]
    o=ProtocolOracle()
    for chunk in chunks: o.feed(chunk)
    actual,p=reconstructed_events(lib,chunks)
    assert actual == o.events
    assert bytes(p.storage[1:]) == bytes(o.cpu.mem_read(o.BUFFER,128))


def test_disabled_parser_drains_without_dispatch(lib):
    o=ProtocolOracle(enabled=False)
    chunks=[b'POWER EDL\nCONFIG_ERASE particle\n']
    for chunk in chunks:o.feed(chunk)
    actual,_=reconstructed_events(lib,chunks,enabled=False)
    assert actual == o.events == []


def test_unknown_hardware_access_is_not_silently_emulated():
    from unicorn import UcError
    o=Oracle()
    with pytest.raises(UcError):
        o.call(0x79d0)  # Watchdog feed touches unmapped MMIO.
