"""One relocatable link must expose missing endpoints and preserve tested ABI."""
import subprocess
from pathlib import Path
import pytest
from build_target_interfaces import build,ROOT
from arm_rebuild_oracle import ArmRebuildOracle

@pytest.fixture(scope='module')
def linked_target_interfaces(tmp_path_factory):
    directory=tmp_path_factory.mktemp('target-interfaces');report=build(directory)
    obj=directory/'target-interfaces.o';elf=directory/'linked.elf'
    base=['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',
        '-Wl,-T,'+str(ROOT/'target/emulation.ld'),'-Wl,-e,syscon_target_uart_read',str(obj)]
    missing=subprocess.run([*base,'-o',str(directory/'missing.elf')],capture_output=True,text=True)
    assert missing.returncode==0,missing.stderr
    assert report['unresolved_symbols']==[]
    # Every dependency is now source-backed; a missing implementation must fail
    # this real final link instead of being satisfied by a test trap.
    (directory/'missing.elf').rename(elf)
    assert subprocess.check_output(['arm-none-eabi-nm','-u',str(elf)],text=True).strip()==''
    assert not report['emulation_endpoint_stubs_included']
    return elf


def test_linked_archive_uart_ring_composition(linked_target_interfaces):
    from test_uart_ring_target import test_uart_receive_irq_and_read_roundtrip_with_real_ring_and_low_level_helpers
    test_uart_receive_irq_and_read_roundtrip_with_real_ring_and_low_level_helpers(linked_target_interfaces)


def test_linked_archive_callback_aliasing_and_memory_order(linked_target_interfaces):
    from test_callback_helpers import test_buffer_callback_order_aliasing_unsigned_limits_and_full_character_return
    test_buffer_callback_order_aliasing_unsigned_limits_and_full_character_return(linked_target_interfaces)


def test_config_assert_binding_forwards_to_actual_target_boundary(linked_target_interfaces):
    candidate=ArmRebuildOracle(linked_target_interfaces);events=[]
    class Boundary(Exception):pass
    def trap(cpu):events.append(tuple(cpu.arg(i) for i in range(3)));raise Boundary()
    candidate.hooks[candidate.symbols['syscon_target_assert']&~1]=trap
    with pytest.raises(Boundary):candidate.call('syscon_cfg_assert',0x20000800,0x87654321,0x20000900)
    assert events==[(0x20000800,0x87654321,0x20000900)]


def test_compiler_memset_binding_executes_reconstructed_memory_function(linked_target_interfaces):
    candidate=ArmRebuildOracle(linked_target_interfaces);address=0x20000800
    for count in (0,1,31,127):
        candidate.put(address,b'\x5a'*160)
        assert candidate.call('memset',address+1,0x123456ab,count)==address+1
        assert candidate.read(address,160)==b'\x5a'+b'\xab'*count+b'\x5a'*(159-count)


def test_source_logger_clock_formatter_and_uart_to_mmio_without_hooks(linked_target_interfaces):
    import struct
    from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_WRITE
    from oracle import Oracle
    original=Oracle();candidate=ArmRebuildOracle(linked_target_interfaces)
    events=[[],[]];bases=[0x40108000,0x40100000]
    for i,cpu in enumerate((original,candidate)):
        for base in bases:cpu.cpu.mem_map(base,0x2000)
        cpu.cpu.mem_map(0x400b0000,0x1000)
        def record(uc,kind,address,size,value,_,i=i):
            if any(base<=address<base+0x2000 for base in bases) or address==0x400b040c:
                if kind!=UC_MEM_WRITE:value=int.from_bytes(uc.mem_read(address,size),'little')
                events[i].append((kind,address,size,value&((1<<(8*size))-1)))
        cpu.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,record)
        cpu.put(0x2000080c,b'\x01');cpu.put(0x2000076a,b'\0');cpu.put(0x20000773,b'\0')
        cpu.put(0x20000678,struct.pack('<Q',0x123456789))
        cpu.put(0x20000900,b'TEST\0');cpu.put(0x20000940,b'value=%u %s\0');cpu.put(0x20000980,b'payload\0')
    for color in [0,1,255]:
        for level in [0,1,2,3,4,5,0xffffffff]:
            for cpu in (original,candidate):cpu.put(0x20000032,bytes([color]))
            events[0].clear();events[1].clear()
            original.call(0x8f88,level,0x20000900,0x20000940,0x87654321,0x20000980)
            candidate.call('syscon_target_logger',level,0x20000900,0x20000940,0x87654321,0x20000980)
            assert events[0]==events[1]
            transmitted=bytes(v for kind,address,size,v in events[0] if kind==UC_MEM_WRITE and address==bases[0]+0x1120)
            assert b'payload' in transmitted and transmitted.endswith(b'\r\n')
    assert not original.hook_calls and not candidate.hook_calls


def test_source_uart_irq_parser_version_and_config_readback_to_uart_mmio(linked_target_interfaces):
    import struct
    from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_WRITE
    from oracle import Oracle
    from test_config_helpers import slot
    original=Oracle();candidate=ArmRebuildOracle(linked_target_interfaces);machines=[original,candidate]
    events=[[],[]];base=0x40108000;context=0x20000840;buffer=0x20000900
    for i,cpu in enumerate(machines):
        cpu.cpu.mem_map(base,0x2000);cpu.cpu.mem_map(0x400b0000,0x1000)
        cpu.cpu.mem_map(0x40081000,0x1000)
        def record(uc,kind,address,size,value,_,i=i):
            if base<=address<base+0x2000 or address in [0x400b040c,0x40081108]:
                if kind!=UC_MEM_WRITE:value=int.from_bytes(uc.mem_read(address,size),'little')
                events[i].append((kind,address,size,value&((1<<(size*8))-1)))
        cpu.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,record)
        cpu.put(0x20000774,bytes(76));cpu.put(0x2000076a,b'\0');cpu.put(0x20000032,b'\0')
        cpu.put(0x2000080c,b'\1');cpu.put(0x20000678,struct.pack('<Q',12345678))
        printer=0x8fa1 if i==0 else cpu.symbols['syscon_target_mfg_logger']|1
        cpu.put(context,struct.pack('<B3xIIBB2xI',0,buffer,0,0,1,printer))
        cpu.put(0xfc00,slot(b'example',b'stored')+b'\xff'*960)
    for command in [b'VERSION\r\n',b'CONFIG_GET:example:;\n',b'HELP\n',b'unknown\n']:
        events[0].clear();events[1].clear()
        # Each byte enters through the real UART interrupt and ring, not a
        # substituted parser read. Command handlers and manufacturing logger run.
        for i,cpu in enumerate(machines):
            for byte in command:
                cpu.put(base+0x1020,struct.pack('<I',11));cpu.put(base+0x1124,struct.pack('<I',byte))
                cpu.call(0x8d70 if i==0 else 'syscon_target_uart_irq',base)
                cpu.call(0x49d0 if i==0 else 'syscon_target_protocol_poll',context,count=2000000)
        assert events[0]==events[1]
        assert bytes(original.cpu.mem_read(0x20000774,76))==candidate.read(0x20000774,76)
        transmitted=bytes(value for kind,address,size,value in events[0] if kind==UC_MEM_WRITE and address==base+0x1120)
        if command.startswith(b'VERSION'):assert b'Version=1.0.52' in transmitted and b'PASS' in transmitted
        if command.startswith(b'CONFIG_GET'):assert b'example = stored' in transmitted and b'PASS' in transmitted
        if command.startswith(b'HELP'):assert b'Available commands:' in transmitted and b'PASS' in transmitted
        if command.startswith(b'unknown'):assert b'Unknown command' in transmitted and b'FAIL' in transmitted
    assert not original.hook_calls and not candidate.hook_calls


def test_actual_runtime_initializer_and_weak_sbrk_original_abi(linked_target_interfaces):
    import struct
    import random
    from oracle import Oracle
    original=Oracle();candidate=ArmRebuildOracle(linked_target_interfaces);rng=random.Random(0x96d4)
    for _ in range(25):
        now=rng.getrandbits(64);dirty=rng.randbytes(64)
        for cpu in (original,candidate):
            cpu.put(0x200002c0,dirty);cpu.put(0x20000678,struct.pack('<Q',now))
        original.call(0x96d4);candidate.call('syscon_target_runtime_init')
        assert bytes(original.cpu.mem_read(0x200002c0,64))==candidate.read(0x200002c0,64)
        increment=rng.getrandbits(32)
        assert original.call(0x76f0,increment)==candidate.call('syscon_rt_sbrk',increment)
    assert not original.hook_calls and not candidate.hook_calls
