import random
import struct
import pytest
from heap_stdio_oracle import RuntimeImage,RuntimePair,REENT,HEAP
@pytest.fixture(scope='module')
def heap_image(tmp_path_factory):return RuntimeImage(tmp_path_factory.mktemp('heap-stdio'))

def test_stock_sbrk_failure_and_large_allocation_errno(heap_image):
    for size in [0,1,4,8,16,1024,0x7fffffff,0xfffffff0,0xffffffff]:
        p=RuntimePair(heap_image)
        assert p.run('syscon_rt_malloc_r',0xa980,REENT,size)==0
    p=RuntimePair(heap_image)
    p.run('syscon_rt_sbrk_r',0xaa88,REENT,0)

def test_allocator_splits_coalesces_alignment_and_realloc_original_overread(heap_image):
    rng=random.Random(0xa980)
    for alignment in range(8):
        p=RuntimePair(heap_image,True,start=HEAP+alignment);live=[]
        for step in range(120):
            if not live or rng.randrange(3)==0:
                size=rng.randrange(0,240);pointer=p.run('syscon_rt_malloc_r',0xa980,REENT,size)
                assert pointer;live.append(pointer)
                usable=p.run('syscon_rt_malloc_usable_size_r',0xaacc,REENT,pointer)
                p.put(pointer,rng.randbytes(min(size,usable)))
            elif rng.randrange(2):
                pointer=live.pop(rng.randrange(len(live)));p.run('syscon_rt_free_r',0xa8ec,REENT,pointer)
            else:
                index=rng.randrange(len(live));pointer=live[index]
                new=p.run('syscon_rt_realloc_r',0xaa3c,REENT,pointer,rng.randrange(0,360))
                if new:live[index]=new
                else:live.pop(index)
        for pointer in live:p.run('syscon_rt_free_r',0xa8ec,REENT,pointer)

def test_sbrk_failure_stages_errno_and_free_overlap_detection(heap_image):
    for fail_at in range(4):
        p=RuntimePair(heap_image,True,start=HEAP+1,fail_at=fail_at,errno=17)
        for size in [32,80,48]:p.run('syscon_rt_malloc_r',0xa980,REENT,size)
    p=RuntimePair(heap_image,True,start=HEAP)
    a=p.run('syscon_rt_malloc_r',0xa980,REENT,40)
    p.run('syscon_rt_free_r',0xa8ec,REENT,a)
    # Original detects overlap when freeing a chunk inside an existing free span.
    p.put(a+12,struct.pack('<I',12));p.run('syscon_rt_free_r',0xa8ec,REENT,a+16)
    p.run('syscon_rt_free_r',0xa8ec,REENT,0)
    for backing in [False,True]:
        p=RuntimePair(heap_image,backing)
        pointer=p.run('syscon_rt_realloc_r',0xaa3c,REENT,0,32)
        if pointer:assert p.run('syscon_rt_realloc_r',0xaa3c,REENT,pointer,0)==0
