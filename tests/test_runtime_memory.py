import random
import pytest
from unicorn import UcError
from oracle import Oracle
from arm_rebuild_oracle import ArmRebuildOracle
from build_arm_test_image import build

ENTRIES={'strcmp':0x263c,'strlen':0x2650,'memcmp':0x972c,'memcpy':0x9748,
         'memset':0x975a,'strchr':0x9828,'strncmp':0x9890,'strncpy':0x98b4,
         'strrchr':0x98dc,'memchr':0xa8b0}
BASE=0x20000a00


@pytest.fixture(scope='module')
def runtime_elf(tmp_path_factory):
    return build(tmp_path_factory.mktemp('runtime-arm'))


class Pair:
    def __init__(self,elf):
        self.original=Oracle();self.arm=ArmRebuildOracle(elf)

    def put(self,data):
        self.original.put(BASE,data);self.arm.put(BASE,data)

    def run(self,name,*args):
        expected=self.original.call(ENTRIES[name],*args)
        got=self.arm.call('syscon_rt_'+name,*args)
        assert got==expected,(name,args,got,expected)
        assert self.arm.read(BASE,768)==bytes(self.original.cpu.mem_read(BASE,768))
        return got


def test_arm_memory_writes_and_overlap_keep_original_forward_order(runtime_elf):
    rng=random.Random(0x9748);p=Pair(runtime_elf)
    for size in (0,1,2,7,31,63,64,127,255):
        for offset in (0,1,3,32,256):
            for source,destination in ((BASE,BASE+offset),(BASE+offset,BASE)):
                p.put(rng.randbytes(768));p.run('memcpy',destination,source,size)
        for value in (0,1,-1,255,256,0x12345678):
            p.put(rng.randbytes(768));p.run('memset',BASE+3,value,size)


def test_arm_string_lengths_comparisons_and_zero_padding(runtime_elf):
    rng=random.Random(0x263c);p=Pair(runtime_elf)
    for _ in range(180):
        size=rng.randrange(128)
        left=bytes(rng.randrange(1,256) for _ in range(size))+b'\0'
        right=bytearray(left)
        if size and rng.randrange(2):right[rng.randrange(size)]=rng.randrange(256)
        data=bytearray(rng.randbytes(768));data[:len(left)]=left
        data[256:256+len(right)]=right
        p.put(data);p.run('strlen',BASE);p.run('strcmp',BASE,BASE+256)
        for n in (0,max(0,size-1),size,size+1,255):
            p.run('memcmp',BASE,BASE+256,n);p.run('strncmp',BASE,BASE+256,n)
            p.put(data);p.run('strncpy',BASE+512,BASE,n);p.put(data)


def test_arm_byte_search_pointer_returns_and_integer_truncation(runtime_elf):
    rng=random.Random(0x9828);p=Pair(runtime_elf)
    for _ in range(4):
        data=bytearray(rng.randbytes(768));data[:256]=bytes(range(1,256))+b'\0'
        # Add repeated high-byte values and an early terminator in some runs.
        data[17]=data[91]=0xfe
        if _:data[rng.randrange(1,200)]=0
        p.put(data)
        for value in list(range(256))+[-1,-2,0x1234,0x100,0x10000]:
            p.run('strchr',BASE,value)
            for size in (0,19,255,256):p.run('memchr',BASE,value,size)
            if value==0 or value&255:p.run('strrchr',BASE,value)


def test_arm_strrchr_nonzero_multiple_of_256_preserves_bad_input_failure(runtime_elf):
    # Original tests the full int for zero before strchr truncates to a byte.
    # 256 therefore searches successive NULs and runs off the mapped SRAM.
    p=Pair(runtime_elf);p.put(bytes(768))
    with pytest.raises(UcError):p.original.call(ENTRIES['strrchr'],BASE,256)
    with pytest.raises(UcError):p.arm.call('syscon_rt_strrchr',BASE,256)
