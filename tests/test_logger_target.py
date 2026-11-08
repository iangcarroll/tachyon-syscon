import gc
import random
import struct
import pytest
from logger_target_oracle import build,LoggerPair
FMT=0x20000400
TAG=0x20000600
ARGS=0x20000300

@pytest.fixture(scope='module',autouse=True)
def own_engines(elf,uart_logger_elf):
    # Compile both fixtures before retaining hundreds of Unicorn mappings.
    # Forking a compiler after that is expensive on macOS.
    gc.collect();LoggerPair.owners=[]
    yield
    LoggerPair.owners=None;gc.collect()

@pytest.fixture(scope='module')
def elf(tmp_path_factory):return build(tmp_path_factory.mktemp('logger-target'))


def test_vlogger_prefix_overreads_original_frame_and_fault_boundary(elf):
    for length in [0,1,20,21,22,23,24,30,31,32,63,64,127,255,300,400,500,590,591,592,600,700]:
        p=LoggerPair(elf,now=123)
        p.put(TAG,b'T'*length+b'\0');p.put(FMT,b'message\0');p.put(ARGS,bytes(32))
        p.call(0x8e8c,'syscon_logger_target_vlog',3,TAG,FMT,ARGS)


def test_wrappers_original_exposed_argument_layout_and_long_prefix(elf):
    for taglength in [1,40,128,300,400]:
        for length in [0,1,31,32,255,256,300]:
            p=LoggerPair(elf,colors=(1,1),now=0xffffffffffffffff)
            p.put(TAG,b'T'*taglength+b'\0');p.put(FMT,b'v'*length+b'\0')
            p.call(0x8f88,'syscon_logger_target',4,TAG,FMT,0x12345678)


def test_variadic_numeric_string_binary_and_sg560d(elf):
    for fmt in [b'%lld %p %s',b'%u %x %lld',b'%cafter',b'%#x %hd %hhd',b'hello',b'x'*128]:
        for entry,symbol in [(0x8f88,'syscon_logger_target'),(0x8fa0,'syscon_logger_target_mfg'),(0x5edc,'syscon_logger_target_sg560d')]:
            p=LoggerPair(elf,colors=(0,1));p.put(FMT,fmt+b'\0');p.put(TAG,b'TAG\0')
            words=(0x1234,0x5678,TAG,TAG,1,2)
            p.call(entry,symbol,*((3,TAG,FMT,*words) if entry==0x8f88 else (FMT,*words)))


def test_live_callback_mutations_and_stack_aliases(elf):
    for mode in ['message','arguments','frame-short','frame-large','saved-r4','saved-return']:
        p=LoggerPair(elf)
        frame=p.SP-368
        p.put(TAG,b'TAG\0');p.put(FMT,b'%s %u\0');p.put(ARGS,struct.pack('<II',TAG,42))
        def mutate(pair,index,port,address,size,mode=mode):
            if address!=frame+24:return
            cpu=pair.cpus[index]
            if mode=='message':cpu.put(FMT,b'changed %u\0')
            elif mode=='arguments':cpu.put(ARGS,struct.pack('<II',FMT,99))
            elif mode=='frame-short':cpu.put(frame+56,b'overwritten\0')
            elif mode=='frame-large':cpu.put(frame+88,b'large stale\0')
            elif mode=='saved-r4':cpu.put(frame+348,struct.pack('<I',0x12345678))
            elif mode=='saved-return':cpu.put(frame+364,struct.pack('<I',0x03000001))
        p.after_write=mutate
        p.call(0x8e8c,'syscon_logger_target_vlog',2,TAG,FMT,ARGS)
    # Source and target destinations intentionally overlap inside the exposed
    # original logger frame. Values are observed afresh after prefix output.
    for offset in [24,56,88,128,320]:
        p=LoggerPair(elf);frame=p.SP-368
        p.put(TAG,b'TAG\0');p.put(FMT,b'%s\0')
        p.put(frame+offset,b'overlapping\0');p.put(ARGS,struct.pack('<I',frame+offset))
        p.call(0x8e8c,'syscon_logger_target_vlog',1,TAG,FMT,ARGS)


def test_snprintf_wrapper_null_destination_alignment_and_overlap(elf):
    output=0x20000900
    for capacity in [0,1,2,8,31,32,255]:
        for destination in [0,output]:
            for fmt,words in [(b'',()),(b'%c-end',(0,)),(b'%lld %s',(0x12345678,0x89abcdef,TAG)),(b'%u %lld',(42,0,0xabcdef,1)),(b'x'*300,())]:
                p=LoggerPair(elf);p.put(FMT,fmt+b'\0');p.put(TAG,b'TAG\0');p.put(output,b'\xa5'*320)
                p.call(0x92f4,'syscon_logger_target_snprintf',destination,capacity,FMT,*words,compare_result=True)
                assert bytes(p.cpus[0].cpu.mem_read(output,320))==bytes(p.cpus[1].cpu.mem_read(output,320))
    for offset in [0,1,4]:
        p=LoggerPair(elf);p.put(FMT,b'abcd\0'+b'\xa5'*40)
        # A cap of one makes the forward-overlap copy terminate without an
        # unbounded self-extension when the writer overtakes the source NUL.
        p.call(0x92f4,'syscon_logger_target_snprintf',FMT+offset,1,FMT,compare_result=True)
        assert bytes(p.cpus[0].cpu.mem_read(FMT,40))==bytes(p.cpus[1].cpu.mem_read(FMT,40))


def test_disabled_logger_and_input_faults(elf):
    p=LoggerPair(elf);p.put(0x2000080c,b'\0')
    p.call(0x8e8c,'syscon_logger_target_vlog',0,0x03000000,0x03000000,0x03000000)
    assert not p.events[0]
    for tag,fmt,args in [(0x03000000,FMT,ARGS),(TAG,0x03000000,ARGS),(TAG,FMT,0x03000000)]:
        p=LoggerPair(elf);p.put(TAG,b'TAG\0');p.put(FMT,b'%u\0');p.put(ARGS,bytes(8))
        p.call(0x8e8c,'syscon_logger_target_vlog',3,tag,fmt,args)


def test_callback_changes_second_pass_and_saved_wrapper_return(elf):
    for mutation in ['format','args','saved-return']:
        p=LoggerPair(elf);frame=p.SP-24-368
        p.put(TAG,b'TAG\0');p.put(FMT,b'%s\0')
        text=0x20000700;p.put(text,b'A'*200+b'\0')
        def mutate(pair,index,port,address,size,mutation=mutation):
            if address!=frame+24:return
            cpu=pair.cpus[index]
            if mutation=='format':cpu.put(FMT,b'B'*80+b'\0')
            elif mutation=='args':cpu.put(pair.SP-4,struct.pack('<I',TAG))
            else:cpu.put(frame+364,struct.pack('<I',0x03000001))
        p.after_write=mutate
        p.call(0x8f88,'syscon_logger_target',3,TAG,FMT,text)


def test_nontrivial_prefix_negative_control(elf):
    from unicorn import UC_PROT_ALL
    p=LoggerPair(elf);p.put(TAG,b'T'*80+b'\0');p.put(FMT,b'message\0');p.put(ARGS,bytes(8))
    candidate=p.cpus[1]
    candidate.cpu.mem_protect(candidate.CODE,0x100000,UC_PROT_ALL)
    candidate.put(candidate.symbols['syscon_logger_target_body']&~1,b'\x70\x47')
    with pytest.raises(AssertionError):p.call(0x8e8c,'syscon_logger_target_vlog',3,TAG,FMT,ARGS)


def test_private_return_normalization_rejects_an_original_address_literal(elf):
    p=LoggerPair(elf,colors=(1,1))
    p.put(TAG,b'T'*400+b'\0');p.put(FMT,b'message\0')
    changed=False
    def stale_return(pair,index,port,address,size):
        nonlocal changed
        if index==1 and size==7 and not changed:
            changed=True
            frame,linked_return=pair.frames[index]
            assert linked_return!=0x8f97
            pair.cpus[index].put(frame+364,struct.pack('<I',0x8f97))
    p.after_write=stale_return
    with pytest.raises(AssertionError,match='Saved return does not match linked call'):
        p.call(0x8f88,'syscon_logger_target',3,TAG,FMT)
    assert changed


def test_logger_strings_are_independent_of_original_rom(elf):
    for entry,symbol,args in [(0x8f88,'syscon_logger_target',(3,TAG,FMT,42)),
                              (0x8fa0,'syscon_logger_target_mfg',(FMT,42)),
                              (0x5edc,'syscon_logger_target_sg560d',(FMT,42))]:
        p=LoggerPair(elf,colors=(1,1))
        p.cpus[1].put(0xe0f4,b'\xa5'*(0xe126-0xe0f4))
        p.cpus[1].put(0xb849,b'\xa5'*5)
        p.cpus[1].put(0xb894,b'\xa5'*3)
        p.put(TAG,b'TAG\0');p.put(FMT,b'number=%u\0')
        p.call(entry,symbol,*args)


def test_color_sequences_signed_time_extremes_and_message_thresholds(elf):
    rng=random.Random(0x8e8c)
    for i in range(60):
        p=LoggerPair(elf,colors=rng.choice([(0,0),(0,1),(1,0),(1,1)]),now=rng.choice([0,1,0x7fffffffffffffff,0x8000000000000000,0xffffffffffffffff]))
        p.put(TAG,b'TAG\0');p.put(FMT,b'x'*rng.choice([0,1,30,31,32,33,254,255,256,257,300])+b'\0');p.put(ARGS,bytes(8))
        p.call(0x8e8c,'syscon_logger_target_vlog',rng.choice([0,1,2,3,4,5,0xffffffff]),TAG,FMT,ARGS)


def test_argument_load_width_order_alignment_and_page_edges(elf):
    from unicorn import UC_HOOK_MEM_READ
    for args in [ARGS,ARGS+1,ARGS+2,ARGS+3,ARGS+4,0x20000ffc,0x20000ffe]:
        for fmt in [b'%u %c %p',b'%hhd %hd',b'%lld %llu',b'%u %lld']:
            p=LoggerPair(elf);p.put(FMT,fmt+b'\0');p.put(TAG,b'TAG\0')
            p.put(ARGS,struct.pack('<8I',1,2,3,4,5,6,7,8))
            accesses=[[],[]]
            for i,cpu in enumerate(p.cpus):
                def read(uc,access,address,size,value,user,i=i):accesses[i].append((address,size))
                cpu.cpu.hook_add(UC_HOOK_MEM_READ,read,begin=args,end=min(args+31,0x20000fff))
            p.call(0x8e8c,'syscon_logger_target_vlog',3,TAG,FMT,args)
            assert accesses[0]==accesses[1],(args,fmt,accesses)


@pytest.fixture(scope='module')
def uart_logger_elf(tmp_path_factory):
    return build(tmp_path_factory.mktemp('logger-real-uart'),real_uart=True)


def test_logger_real_uart_mmio_and_all_output_registers(uart_logger_elf):
    from logger_target_oracle import REGS
    for enabled in (0,1):
        for disabled in (0,1):
            for colors in [(0,0),(1,1)]:
                for entry,symbol in [(0x8e8c,'syscon_logger_target_vlog'),(0x8f88,'syscon_logger_target'),(0x8fa0,'syscon_logger_target_mfg'),(0x5edc,'syscon_logger_target_sg560d')]:
                    p=LoggerPair(uart_logger_elf,colors=colors,real_uart=True)
                    p.put(0x2000080c,bytes([enabled]));p.put(0x2000076a,bytes([disabled]));p.put(0x20000773,bytes([disabled]))
                    p.put(TAG,b'TAG\0');p.put(FMT,b'%u message\0');p.put(ARGS,struct.pack('<I',123))
                    args=(3,TAG,FMT,ARGS) if entry==0x8e8c else (3,TAG,FMT,123) if entry==0x8f88 else (FMT,123)
                    p.call(entry,symbol,*args)
                    left=[p.cpus[0].cpu.reg_read(r) for r in REGS[:4]]
                    right=[p.cpus[1].cpu.reg_read(r) for r in REGS[:4]]
                    if entry==0x8fa0 and not enabled:
                        # Disabled manufacturing logging leaves its tag in R1.
                        # Validate the linked object and contents, not its old PC.
                        assert right[1]==p.cpus[1].symbols['syscon_log_mfg_tag']
                        assert p.cpus[0].cstring(left[1])==p.cpus[1].cstring(right[1])
                        right[1]=left[1]
                    assert left==right,(entry,enabled,disabled,colors,left,right)
