"""Original ARM initialization/compaction/update through rebuilt FLASHCTL."""
import gc
import struct
import pytest
from config_helpers_oracle import build,ConfigHelperPair
from test_config_helpers import controller_pair,compare_controllers,slot,string,KEY,VALUE,OUT,SLOTPTR

@pytest.fixture(scope='module',autouse=True)
def own_engines():
    gc.collect();ConfigHelperPair.owners=[]
    yield
    ConfigHelperPair.owners=None;gc.collect()

@pytest.fixture(scope='module')
def elf(tmp_path_factory):return build(tmp_path_factory.mktemp('config-target-updates'))


def test_initialization_preserves_existing_versions_and_loads_runtime(elf):
    for identity in [b'',b'1',b'old-version']:
        for runtime in [b'',b'1',b'new-version']:
            p=controller_pair(elf)
            if identity:p.put(0xf800,slot(b'confVersion',identity)+slot(b'hw_revision',b'1.2.0')+b'\xff'*896)
            if runtime:p.put(0xfc00,slot(b'confVersion',runtime)+slot(b'sys.auto_boot',b'true')+b'\xff'*896)
            p.call(0x30f0,'syscon_target_config_init',returns=False);compare_controllers(p)
            p.call(0x30f0,'syscon_target_config_init',returns=False);compare_controllers(p)
            assert not p.original.hook_calls and not p.candidate.hook_calls
    # Get ignores checksum validity, so a found corrupt version prevents erase.
    p=controller_pair(elf);record=slot(b'confVersion',b'garbage');record[63]^=1
    p.put(0xfc00,record+b'\xff'*960)
    p.call(0x2fa0,'syscon_cfg_store_init',0xfc00,960,returns=False);compare_controllers(p)
    assert not p.controllers[0].events


def test_updates_across_repeated_compactions_and_unchanged_cache(elf):
    p=controller_pair(elf)
    p.call(0x30f0,'syscon_target_config_init',returns=False)
    for i in range(70):
        key=[b'sys.auto_boot',b'sys.edl_timer',b'user.mode',b'user.empty'][i%4]
        value=[b'true' if i%8 else b'false',str(i).encode(),b'mode'+str(i).encode(),b''][i%4]
        p.put(KEY,key+b'\0');p.put(VALUE,value+b'\0')
        p.call(0x32c8,'syscon_cfg_runtime_update',KEY,VALUE);compare_controllers(p)
        p.put(OUT,b'\xa5'*64);p.call(0x339c,'syscon_cfg_runtime_get',KEY,OUT);p.equal(OUT,64)
    # Identical stored text returns early; pre-existing cached runtime bytes stay.
    p.put(KEY,b'user.mode\0');p.put(VALUE,b'same\0')
    p.call(0x32c8,'syscon_cfg_runtime_update',KEY,VALUE)
    p.put(0x20000030,b'\xa5'*22)
    p.call(0x32c8,'syscon_cfg_runtime_update',KEY,VALUE);compare_controllers(p)
    assert p.candidate.read(0x20000030,22)==b'\xa5'*22
    assert not p.original.hook_calls and not p.candidate.hook_calls


def test_compaction_capacity_corruption_delimiters_and_empty_value(elf):
    for unique in [1,2,7,8,9,15]:
        for corruption in ['none','key_checksum','value_checksum','invalid_key','invalid_value','semicolon']:
            p=controller_pair(elf);data=bytearray(b'\xff'*1024)
            for i in range(15):data[i*64:(i+1)*64]=slot(f'key{i%unique}'.encode(),f'value{i}'.encode())
            if corruption=='key_checksum':data[14*64+31]^=1
            if corruption=='value_checksum':data[14*64+63]^=1
            if corruption=='invalid_key':data[14*64:15*64]=slot(b'bad!',b'value')
            if corruption=='invalid_value':data[14*64:15*64]=slot(b'legacy',b'with spaces!')
            if corruption=='semicolon':data[14*64:15*64]=slot(b'legacy;tail',b'value;tail')
            p.put(0xfc00,data);p.put(KEY,b'new\0');p.put(VALUE,b'\0')
            p.call(0x32c8,'syscon_cfg_runtime_update',KEY,VALUE);compare_controllers(p)
            assert not p.original.hook_calls and not p.candidate.hook_calls


@pytest.mark.parametrize('failure',[*[('erase',i) for i in [1,8,15]],*[('blank',i) for i in range(1,9)],*[('program',i) for i in range(1,65)]])
def test_compaction_each_restore_failure_preserves_prior_flash_effects(elf,failure):
    p=controller_pair(elf,failure);data=bytearray(b'\xff'*1024)
    for i in range(15):data[i*64:(i+1)*64]=slot(f'old{i%7}'.encode(),f'v{i}'.encode())
    p.put(0xfc00,data);p.put(KEY,b'new\0');p.put(VALUE,b'value\0')
    p.call(0x32c8,'syscon_cfg_runtime_update',KEY,VALUE);compare_controllers(p)
    assert not p.original.hook_calls and not p.candidate.hook_calls


def test_bool_integer_parsers_original_abi_and_unchanged_output(elf):
    p=controller_pair(elf)
    for value in [b'',b'true',b'false',b'1',b'0',b'True',b'+3',b'-0',b'-1',b' 3',b'3 ',b'2147483647',b'2147483648',b'999999999999999999999999999',b'3tail']:
        p.put(0xfc00,slot(b'key',value)+b'\xff'*960);p.put(KEY,b'key\0');p.put(OUT,b'\xa5'*8)
        p.call(0x2d08,'syscon_cfg_bool_get',0xfc00,KEY,OUT,returns=False);p.equal(OUT,8)
        p.call(0x2d94,'syscon_cfg_u32_get',0xfc00,KEY,OUT,returns=False);p.equal(OUT,8);p.equal(0x20000280,4)
    assert not p.original.hook_calls and not p.candidate.hook_calls


def bind_diagnostic_ports(p):
    p.put(0x2000080c,b'\1')
    p.bind(0x312c,'syscon_target_color',lambda cpu,events:events.append(('color',0)) or 0)
    def clock(cpu,events):
        from unicorn.arm_const import UC_ARM_REG_R1
        cpu.cpu.reg_write(UC_ARM_REG_R1,0);events.append(('time',0));return 0
    p.bind(0x77b4,'syscon_target_now',clock)
    def write(cpu,events):
        address,size=(cpu.arg(0),cpu.arg(1)) if cpu is p.original else (cpu.arg(1),cpu.arg(2))
        events.append(('uart',bytes(cpu.cpu.mem_read(address,size))))
    p.bind(0x3af4,'syscon_target_uart_write',write)


def test_enabled_compaction_and_initialization_diagnostic_output(elf):
    for direct in [True,False]:
        for unique in [1,7,8,9]:
            p=controller_pair(elf);bind_diagnostic_ports(p)
            data=bytearray(b'\xff'*1024)
            for i in range(15):data[i*64:(i+1)*64]=slot(f'old{i%unique}'.encode(),f'v{i}'.encode())
            p.put(0xfc00,data);p.put(KEY,b'new\0');p.put(VALUE,b'value\0')
            if direct:p.call(0x2abc,'syscon_cfg_compact',0xfc00,KEY,VALUE,same_stack=True)
            else:p.call(0x32c8,'syscon_cfg_runtime_update',KEY,VALUE,same_stack=True)
            compare_controllers(p)
    p=controller_pair(elf);bind_diagnostic_ports(p)
    p.call(0x30f0,'syscon_target_config_init',returns=False,same_stack=True)
    p.call(0x30f0,'syscon_target_config_init',returns=False,same_stack=True)
    compare_controllers(p)


def test_legacy_format_compaction_uses_original_live_argument_frame(elf):
    # Semicolon terminates field validation but the legacy key retains its
    # suffix. Both format strings therefore consume the omitted variadic word.
    # Pointer-valued output must be compared at the same physical incoming SP.
    for key,value in [(b'legacy',b'%u'),(b'legacy;%u',b'literal')]:
        p=controller_pair(elf)
        p.put(0xfc00,bytes(slot(key,value))*15+b'\xff'*64)
        p.put(KEY,b'new\0');p.put(VALUE,b'value\0')
        p.call(0x32c8,'syscon_cfg_runtime_update',KEY,VALUE,same_stack=True)
        compare_controllers(p)
        assert bytes(p.original.cpu.mem_read(0xfc00,1024))==p.candidate.read(0xfc00,1024)


def test_initializer_ignores_intermediate_failures_and_asserts_after_lookup(elf):
    for failure in [('erase',1),('erase',10),('blank',1),('program',1),('program',4),('program',8)]:
        p=controller_pair(elf,failure)
        # Not erased initially: an erase error can leave no place for append.
        p.put(0xfc00,b'\0'*1024)
        def assertion(cpu,events):
            events.append(('assert',string(cpu,cpu.arg(0)),cpu.arg(1),string(cpu,cpu.arg(2))))
            return 0 # Deliberate returning boundary, not simulated reset.
        p.bind(0x2678,'syscon_cfg_assert',assertion)
        p.call(0x2fa0,'syscon_cfg_store_init',0xfc00,960,returns=False)
        compare_controllers(p)


def test_runtime_update_validation_status_and_no_reload_dependencies(elf):
    from test_config_helpers import bind_logger
    for writable in [0,1,2,0xffffffff]:
        for found in [0,1,2,0xffffffff]:
            p=ConfigHelperPair(elf);bind_logger(p)
            p.put(KEY,b'key\0');p.put(VALUE,b'value\0')
            p.bind(0x2810,'syscon_cfg_field_writable',lambda cpu,events:writable)
            def get(cpu,events):cpu.put(cpu.arg(3),b'value\0');return found
            p.bind(0x2cb8,'syscon_cfg_store_get',get)
            def find(cpu,events):cpu.put(cpu.arg(4),struct.pack('<I',0xfc00));return 1
            p.bind(0x29a0,'syscon_cfg_find_slot',find)
            p.bind(0x28d4,'syscon_cfg_write_slot',lambda cpu,events:events.append(('write-slot',)) or 9)
            p.bind(0x2df8,'syscon_cfg_load',lambda cpu,events:events.append(('load',)) or 0)
            p.call(0x32c8,'syscon_cfg_runtime_update',KEY,VALUE)


def test_direct_compaction_truncation_and_runtime_input_validation(elf):
    for key,value in [(b'',b''),(b'k'*30,b'v'*30),(b'k'*31,b'v'*31),(b'k'*80,b'v'*90),(b'bad!key',b'non-readable value')]:
        p=controller_pair(elf);p.put(KEY,key+b'\0');p.put(VALUE,value+b'\0')
        p.call(0x2abc,'syscon_cfg_compact',0xfc00,KEY,VALUE);compare_controllers(p)
    for key,value in [(b'',b'v'),(b'k'*31,b'v'),(b'k',b'v'*31),(b'bad%',b'v'),(b'bad;',b'v'),(b'key',b'bad value'),(b'key',b'')]:
        p=controller_pair(elf);p.put(KEY,key+b'\0');p.put(VALUE,value+b'\0')
        p.bind(0x2678,'syscon_cfg_assert',lambda cpu,events:events.append(('assert',cpu.arg(1))) or 0)
        p.call(0x32c8,'syscon_cfg_runtime_update',KEY,VALUE);compare_controllers(p)


def test_compaction_no_restore_slot_and_raw_return_status_boundaries(elf):
    from test_config_helpers import bind_logger
    for find_status in [0,1,9,0xffffffff]:
        for write_status in [0,1,9,0xffffffff]:
            p=controller_pair(elf);bind_logger(p)
            p.put(KEY,b'new\0');p.put(VALUE,b'value\0')
            p.bind(0x27a8,'syscon_cfg_store_erase',lambda cpu,events:events.append(('erase',cpu.arg(0),cpu.arg(1))) or 7)
            def find(cpu,events):
                cpu.put(cpu.arg(4),struct.pack('<I',0xfc00));events.append(('find',cpu.arg(0),cpu.arg(1),cpu.arg(2),cpu.arg(3)));return find_status
            p.bind(0x29a0,'syscon_cfg_find_slot',find)
            def write(cpu,events):events.append(('write',cpu.arg(0),string(cpu,cpu.arg(1),31),string(cpu,cpu.arg(2),31)));return write_status
            p.bind(0x28d4,'syscon_cfg_write_slot',write)
            p.call(0x2abc,'syscon_cfg_compact',0xfc00,KEY,VALUE)
