"""Discovered string EOF callback and its observable sscanf FILE field."""
import gc
import random
import struct
import pytest
from unicorn import UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3
from oracle import Oracle
from arm_rebuild_oracle import ArmRebuildOracle
from build_runtime_scan_image import build
from elftools.elf.elffile import ELFFile

INPUT=0x20000300
FORMAT=0x20000400
OUT=0x20000500
REENT=0x20000100

@pytest.fixture(scope='module')
def image(tmp_path_factory):return build(tmp_path_factory.mktemp('scan-callback'))
@pytest.fixture(scope='module',autouse=True)
def owners():
    gc.collect();engines=[]
    yield engines
    engines.clear();gc.collect()

def pair(image,owners):
    cpus=[Oracle(),ArmRebuildOracle(image)];owners.extend(cpus)
    for cpu in cpus:cpu.put(0x20000258,struct.pack('<I',REENT))
    return cpus


def test_seofread_exact_emitted_body_and_direct_abi(image,owners):
    reference,rebuilt=pair(image,owners);entry=rebuilt.symbols['syscon_rt_seofread']&~1
    with image.open('rb') as stream:
        symbol=ELFFile(stream).get_section_by_name('.symtab').get_symbol_by_name('syscon_rt_seofread')[0]
        assert symbol['st_size']==4
    assert bytes(reference.cpu.mem_read(0x9824,4))==rebuilt.read(entry,4)
    rng=random.Random(0x9824)
    # Invalid pointers are intentional: this callback never dereferences them.
    for args in [(0,0,0,0),(0xffffffff,0xffffffff,0xffffffff,0xffffffff)]+[tuple(rng.getrandbits(32) for _ in range(4)) for _ in range(40)]:
        before=[bytes(cpu.cpu.mem_read(0x20000000,4096)) for cpu in (reference,rebuilt)]
        assert reference.call(0x9824,*args)==rebuilt.call('syscon_rt_seofread',*args)==0
        for cpu,ram in zip((reference,rebuilt),before):
            assert bytes(cpu.cpu.mem_read(0x20000000,4096))==ram
            assert tuple(cpu.cpu.reg_read(r) for r in [UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3])==args[1:]


@pytest.mark.parametrize('text',[b'',b'12345',b'12\0ignored'])
@pytest.mark.parametrize('alias',[False,True])
def test_sscanf_constructed_fields_and_read_callback_alias(image,owners,text,alias):
    cpus=pair(image,owners);snapshots=[None,None];streams=[None,None]
    # Exact fields initialized by original97d4. Other fields were uninitialized
    # originally; do not add a blanket memset that silently changes them.
    regions=[(0,8),(12,12),(36,4),(52,4),(72,4)]
    for index,cpu in enumerate(cpus):
        cpu.put(INPUT,text+b'\0');cpu.put(FORMAT,b'%n%d\0' if alias else b'%d\0');cpu.put(OUT,b'\xa5'*8)
        entry=0x9ddc if index==0 else cpu.symbols['syscon_rt_vfscanf']&~1
        def observe(uc,address,size,user,index=index,cpu=cpu):
            stream=cpu.arg(1);streams[index]=stream
            snapshots[index]=[bytes(uc.mem_read(stream+offset,length)) for offset,length in regions]
            # Alias the first destination to the original/rebuilt live FILE
            # callback field. The actual scanner body handles this write.
            if alias:uc.mem_write(cpu.arg(3),struct.pack('<I',stream+36))
        cpu.cpu.hook_add(UC_HOOK_CODE,observe,begin=entry,end=entry)
    expected=cpus[0].call(0x97d4,INPUT,FORMAT,OUT,OUT+4)
    actual=cpus[1].call('syscon_rt_sscanf',INPUT,FORMAT,OUT,OUT+4)
    assert actual==expected
    callback_original=struct.unpack('<I',snapshots[0][2])[0]
    callback_rebuilt=struct.unpack('<I',snapshots[1][2])[0]
    assert callback_original==0x9825
    assert callback_rebuilt==cpus[1].symbols['syscon_rt_seofread']|1
    snapshots[1][2]=struct.pack('<I',callback_original)
    assert snapshots[0]==snapshots[1]
    if alias:
        assert cpus[0].u32(streams[0]+36)==cpus[1].u32(streams[1]+36)==0
    assert bytes(cpus[0].cpu.mem_read(OUT,8))==cpus[1].read(OUT,8)
    # Call the captured constructor callback even if %n subsequently replaced
    # its FILE field. Both concrete functions must return EOF-read count zero.
    assert cpus[0].call(callback_original,REENT,0,OUT,8)==cpus[1].call(callback_rebuilt,REENT,0,OUT,8)==0
