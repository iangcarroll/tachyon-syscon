import random
import struct
import subprocess
import pytest
from pathlib import Path
from arm_rebuild_oracle import ArmRebuildOracle
from oracle import Oracle

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def support_elf(tmp_path_factory):
    dest=tmp_path_factory.mktemp('runtime-support')
    trap=dest/'traps.c'
    trap.write_text('void syscon_rt_strtol(void){__asm__("bkpt #0");}\n'
                    'void syscon_rt_strtoul_r(void){__asm__("bkpt #0");}\n')
    elf=dest/'test.elf'
    subprocess.run(['arm-none-eabi-gcc','-std=c11','-Os','-mcpu=cortex-m0plus','-mthumb',
        '-ffreestanding','-fno-builtin','-nostdlib','-Wall','-Wextra','-Werror',
        '-I',str(ROOT/'include'),str(ROOT/'target/runtime_support.c'),str(trap),
        '-Wl,-T,'+str(ROOT/'target/emulation.ld'),'-Wl,-e,syscon_rt_memmove','-o',str(elf)],check=True)
    return elf


def test_support_ctype_preserves_table_values_including_readable_out_of_domain(support_elf):
    o=Oracle();a=ArmRebuildOracle(support_elf);rng=random.Random(0x971c)
    values=list(range(-1,256))+[rng.randrange(-0xe127,0x10000-0xe127) for _ in range(500)]
    for n in values:
        for entry,name in [(0x971c,'isalnum'),(0x9a40,'toupper')]:
            assert a.call('syscon_rt_'+name,n)==o.call(entry,n),(name,n)


def test_support_exit_registration_is_absent_and_locks_do_not_access_memory(support_elf):
    o=Oracle();a=ArmRebuildOracle(support_elf);rng=random.Random(0x96b8)
    for _ in range(100):
        args=[rng.getrandbits(32) for _ in range(3)]
        for entry,name in [(0x969c,'arm_atexit'),(0x96b8,'cxa_atexit')]:
            assert a.call('syscon_rt_'+name,*args)==o.call(entry,*args)==0
        for entry,name in [(0xa8ac,'lock_acquire'),(0xa8ae,'lock_release')]:
            before=a.state();a.call('syscon_rt_'+name,args[0]);o.call(entry,args[0])
            assert a.state()==before


def test_support_getreent_reads_live_pointer_and_wrappers_forward_real_arm_arguments(support_elf):
    o=Oracle();a=ArmRebuildOracle(support_elf);rng=random.Random(0x9a54)
    for _ in range(30):
        value=rng.getrandbits(32);raw=struct.pack('<I',value)
        o.put(0x20000258,raw);a.put(0x20000258,raw)
        assert a.call('syscon_rt_getreent')==o.call(0x9a54)==value
    for entry,name,dependency,argc in [(0x96aa,'atoi',0x9a28,3),(0xa828,'strtoul_alias',0xa714,4)]:
        events=[[],[]]
        def reference(cpu):events[0].append(tuple(cpu.arg(i) for i in range(argc)));return 0x98765432
        def rebuilt(cpu):events[1].append(tuple(cpu.arg(i) for i in range(argc)));return 0x98765432
        o.hooks[dependency]=reference
        symbol='syscon_rt_strtol' if name=='atoi' else 'syscon_rt_strtoul_r'
        a.hooks[a.symbols[symbol]&~1]=rebuilt
        for _ in range(30):
            args=[rng.getrandbits(32) for _ in range(1 if name=='atoi' else 4)]
            assert a.call('syscon_rt_'+name,*args)==o.call(entry,*args)==0x98765432
        assert events[0]==events[1]


def test_support_memmove_overlap_direction_returns_and_all_guard_bytes(support_elf):
    o=Oracle();a=ArmRebuildOracle(support_elf);rng=random.Random(0xa8c6);base=0x20000900
    for size in (0,1,2,3,31,64,127,255):
        for delta in (0,1,2,31,64,256):
            for destination,source in [(base,base+delta),(base+delta,base)]:
                data=rng.randbytes(768);o.put(base,data);a.put(base,data)
                assert a.call('syscon_rt_memmove',destination,source,size)==o.call(0xa8c6,destination,source,size)
                assert a.read(base,768)==bytes(o.cpu.mem_read(base,768))
