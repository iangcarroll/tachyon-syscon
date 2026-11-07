import random
import struct
import pytest
from config_helpers_oracle import build,ConfigHelperPair,logger_arguments
KEY=0x20000500
VALUE=0x20000580
OUT=0x20000600
SLOT=0x20000700
SLOTPTR=0x20000640


@pytest.fixture(scope='module',autouse=True)
def keep_unicorn_engines_alive():
    # Explicitly retain every paired engine until this module has completed.
    # Engine finalization interleaved with other live JIT engines has caused
    # native Unicorn crashes on macOS; collect only outside emulation.
    import gc
    gc.collect()
    ConfigHelperPair.owners=[]
    yield
    ConfigHelperPair.owners=None
    gc.collect()

@pytest.fixture(scope='module')
def config_elf(tmp_path_factory):return build(tmp_path_factory.mktemp('config-helpers'))

def string(cpu,address,limit=1000):
    data=bytes(cpu.cpu.mem_read(address,limit));return data.split(b'\0')[0]

def slot(key,value):
    result=bytearray(b'\xff'*64)
    for start,text in [(0,key),(32,value)]:
        result[start:start+len(text)+1]=text+b'\0';checksum=0
        for b in result[start:start+31]:checksum^=b
        result[start+31]=checksum
    return result

def bind_logger(p):
    def log(cpu,events):
        events.append(('log',logger_arguments(cpu)));return 0
    p.bind(0x8f88,'syscon_target_logger',log)

def test_namespace_blank_scans_every_byte_and_does_not_read_invalid_indices(config_elf):
    p=ConfigHelperPair(config_elf)
    for entry,name,base,count in [(0x3098,'syscon_cfg_runtime_slot_blank',0xfc00,15),(0x30c0,'syscon_cfg_identity_slot_blank',0xf800,16)]:
        p.put(base,b'\xff'*(count*64))
        for index in range(count):
            assert p.call(entry,name,index)==1
            for byte in range(64):
                p.put(base+64*index+byte,b'\x00');assert p.call(entry,name,index)==0
                p.put(base+64*index+byte,b'\xff')
        for index in [count,count+1,0x3ffffff,0x4000000,0x80000000,0xffffffff]:assert p.call(entry,name,index)==1
    p.call(0x30e8,'syscon_cfg_runtime_slot_count');p.call(0x30ec,'syscon_cfg_identity_slot_count')


def test_indexed_get_original_fifth_argument_and_status_forwarding(config_elf):
    p=ConfigHelperPair(config_elf);bind_logger(p);responses={'find':0,'read':0}
    def find(cpu,events):
        events.append(('find',tuple(cpu.arg(i) for i in range(4)),cpu.u32(cpu.arg(4))))
        cpu.put(cpu.arg(4),struct.pack('<I',SLOT));return responses['find']
    def read(cpu,events):events.append(('read',cpu.arg(0),cpu.arg(1)));cpu.put(cpu.arg(1),b'X'*32);return responses['read']
    p.bind(0x29a0,'syscon_cfg_find_slot',find);p.bind(0x296c,'syscon_cfg_read_slot',read)
    for entry,name,args in [(0x3048,'syscon_cfg_indexed_get',(0xf800,1024)),(0x32b0,'syscon_cfg_identity_indexed_get',()),(0x3464,'syscon_cfg_runtime_indexed_get',())]:
        for length in [0,1,30,31,32,64]:
            for find_status in [0,1,2,0xffffffff]:
                for read_status in [0,1,7,0xffffffff]:
                    responses.update(find=find_status,read=read_status)
                    p.put(KEY,b'k'*length+b'\0');p.put(OUT,b'\xa5'*64)
                    p.call(entry,name,*args,KEY,OUT);p.equal(OUT,64)


def test_namespace_get_append_and_erase_dependency_sequences(config_elf):
    p=ConfigHelperPair(config_elf);bind_logger(p);responses={'erase':0,'append':0,'get':0}
    for address,symbol,label,n in [(0x27a8,'syscon_cfg_store_erase','erase',2),(0x2f0c,'syscon_cfg_store_append','append',4)]:
        def dependency(cpu,events,label=label,n=n):
            args=tuple(cpu.arg(i) for i in range(n))
            if label=='append':args=args[:2]+(string(cpu,args[2]),string(cpu,args[3]))
            events.append((label,args));return responses[label]
        p.bind(address,symbol,dependency)
    def get(cpu,events):
        target=cpu.arg(3);events.append(('get',(cpu.arg(0),cpu.arg(1),string(cpu,cpu.arg(2))),target if target==OUT else 'local32'))
        cpu.put(target,b'V'*32);return responses['get']
    p.bind(0x2cb8,'syscon_cfg_store_get',get)
    p.bind(0x2df8,'syscon_cfg_load',lambda cpu,events:events.append(('load',)) or 0)
    def assertion(cpu,events):events.append(('assert',string(cpu,cpu.arg(0)),cpu.arg(1),string(cpu,cpu.arg(2))));return 0
    p.bind(0x2678,'syscon_cfg_assert',assertion)
    p.put(KEY,b'key\0');p.put(VALUE,b'value\0')
    for status in [0,1,2,0xffffffff]:
        responses['get']=status;responses['append']=status
        for entry,name in [(0x3298,'syscon_cfg_identity_get'),(0x339c,'syscon_cfg_runtime_get')]:p.call(entry,name,KEY,OUT);p.equal(OUT,32)
        p.call(0x3278,'syscon_cfg_identity_append',KEY,VALUE)
    for entry,name,password in [(0x31d0,'syscon_cfg_identity_erase',b'B23000'),(0x33b4,'syscon_cfg_runtime_erase',b'particle')]:
        for attempted in [b'',b'wrong',password.lower(),password,password+b'!',password+b'\0suffix']:
            p.put(KEY,attempted+b'\0')
            for erase in [0,1,0xffffffff]:
                for append in [0,1,9,0xffffffff]:
                    for get in [0,1,2]:
                        responses.update(erase=erase,append=append,get=get);p.call(entry,name,KEY)


def test_full_indexed_get_and_key_get_preserve_legacy_invalid_slot_behavior(config_elf):
    p=ConfigHelperPair(config_elf);bind_logger(p)
    for base,count in [(0xf800,16),(0xfc00,15)]:
        initial=bytearray(b'\xff'*1024)
        for i in range(count):initial[64*i:64*i+64]=slot(f'key{i}'.encode(),f'value{i}'.encode())
        for corruption in ['none','key_checksum','value_checksum','value_char','key_char','semicolon']:
            data=initial[:]
            if corruption=='key_checksum':data[31]^=1
            if corruption=='value_checksum':data[63]^=1
            if corruption=='value_char':data[32]=ord('%')
            if corruption=='key_char':data[0]=0xff
            if corruption=='semicolon':data[:64]=slot(b'key0;tail',b'value;rest')
            p.put(base,data)
            for indexed in [True,False]:
                indices=[b'',b'0',b'+0',b'-1',b'notnumber',b'1tail',str(count-1).encode(),str(count).encode(),b'2147483648'] if indexed else [b'key0',b'key1',b'missing',b'k'*31]
                for key in indices:
                    p.put(KEY,key+b'\0'+b'\xa5'*40);p.put(OUT,b'\xa5'*64)
                    if indexed:
                        entry,name=(0x32b0,'syscon_cfg_identity_indexed_get') if base==0xf800 else (0x3464,'syscon_cfg_runtime_indexed_get')
                    else:entry,name=(0x3298,'syscon_cfg_identity_get') if base==0xf800 else (0x339c,'syscon_cfg_runtime_get')
                    p.call(entry,name,KEY,OUT);p.equal(KEY,64);p.equal(OUT,64);p.equal(0x20000280,4)


def test_shared_read_helpers_random_corrupt_fields_and_mode0_boundaries(config_elf):
    p=ConfigHelperPair(config_elf);bind_logger(p);rng=random.Random(0x2840)
    for _ in range(300):
        raw=bytearray(rng.randbytes(64))
        if rng.randrange(2):raw=slot(rng.choice([b'a',b'',b'A-z_9.',b'key']),rng.choice([b'1',b'',b'v;tail',b'bad%']))
        if rng.randrange(3)==0:raw[rng.randrange(64)]^=1
        p.put(SLOT,raw);p.put(OUT,b'\xa5'*64)
        p.call(0x27dc,'syscon_cfg_field_readable',SLOT);p.call(0x282c,'syscon_cfg_checksum',SLOT)
        p.call(0x2840,'syscon_cfg_slot_valid',SLOT);p.call(0x296c,'syscon_cfg_read_slot',SLOT,OUT);p.equal(OUT,64)
    for count in [1,2,3]:
        for blank in range(count):
            p.put(SLOT,bytes(count*64));p.put(SLOT+64*blank,b'\xff'*64);p.put(SLOTPTR,b'\xa5'*4)
            p.call(0x29a0,'syscon_cfg_find_slot',SLOT,count*64+63,0,0,SLOTPTR);p.equal(SLOTPTR,4)


def controller_pair(config_elf,fail=None):
    from flash_controller_oracle import attach_controller
    p=ConfigHelperPair(config_elf)
    # API-side peripheral writes mutate flash during a status-read callback.
    # Keep it non-executable while allowing the model to update its backing.
    from unicorn import UC_PROT_READ,UC_PROT_WRITE,UC_HOOK_MEM_WRITE
    p.candidate.cpu.mem_protect(0,0x10000,UC_PROT_READ|UC_PROT_WRITE)
    def unexpected_cpu_flash_write(uc,access,address,size,value,user):
        raise AssertionError(('CPU wrote flash outside FLASHCTL',address,size,value))
    p.candidate.cpu.hook_add(UC_HOOK_MEM_WRITE,unexpected_cpu_flash_write,begin=0,end=0xffff)
    p.put(0x2000080c,b'\0') # Run both complete logger bodies with logging disabled.
    p.controllers=[attach_controller(cpu,busy=(4,0,2),fail=fail) for cpu in (p.original,p.candidate)]
    p.put(0xf800,b'\xff'*2048)
    return p


def compare_controllers(p):
    a,b=p.controllers
    assert a.trace==b.trace
    assert a.events==b.events
    assert a.registers==b.registers
    p.equal(0xf800,2048);p.equal(0x20000030,22);p.equal(0x20000280,4)


def test_append_read_load_erase_full_source_to_mmio_without_endpoint_hooks(config_elf):
    p=controller_pair(config_elf)
    # Body calls are genuine across namespace, append, validation, searching,
    # newlib output, FLASHCTL, configuration loading and logger disabled paths.
    for key,value in [(b'hw_revision',b'v1.2'),(b'plain',b''),(b'plain',b'123'),
                      (b'_',b'-.'),(b'a'*30,b'v'*30),(b'bad%',b'v'),
                      (b'key',b'bad;tail'),(b'k'*31,b'v')]:
        p.put(KEY,key+b'\0');p.put(VALUE,value+b'\0')
        p.call(0x3278,'syscon_cfg_identity_append',KEY,VALUE);compare_controllers(p)
        if key and b'%' not in key:
            p.put(OUT,b'\xa5'*64);p.call(0x3298,'syscon_cfg_identity_get',KEY,OUT);p.equal(OUT,64)
    # Repeated appends fill every available record; latest matching key wins.
    for i in range(18):
        p.put(KEY,b'repeat\0');p.put(VALUE,str(i).encode()+b'\0')
        p.call(0x3278,'syscon_cfg_identity_append',KEY,VALUE);compare_controllers(p)
    for entry,name,password in [(0x31d0,'syscon_cfg_identity_erase',b'B23000'),(0x33b4,'syscon_cfg_runtime_erase',b'particle')]:
        p.put(KEY,password+b'\0');p.call(entry,name,KEY);compare_controllers(p)
    assert not p.original.hook_calls and not p.candidate.hook_calls
    # Intentional broken compiled helper must be detected by the integrated read.
    from unicorn.unicorn_const import UC_PROT_ALL
    p=controller_pair(config_elf) # Fresh CPU: avoid patching an already translated block.
    p.put(0xf800,slot(b'valid',b'value')+b'\xff'*960)
    p.candidate.cpu.mem_protect(p.candidate.CODE,0x100000,UC_PROT_ALL)
    p.candidate.put(p.candidate.symbols['syscon_cfg_checksum']&~1,b'\x00\x20\x70\x47')
    p.put(KEY,b'0\0');p.put(OUT,b'\xa5'*64)
    with pytest.raises(AssertionError):p.call(0x32b0,'syscon_cfg_identity_indexed_get',KEY,OUT)


@pytest.mark.parametrize('fail',[('blank',1),*[('program',i) for i in range(1,9)],('erase',1),('erase',8),('erase',16)])
def test_real_flash_failure_and_partial_programming(config_elf,fail):
    p=controller_pair(config_elf,fail)
    p.put(KEY,b'key\0');p.put(VALUE,b'value\0')
    if fail[0]=='erase':p.call(0x27a8,'syscon_cfg_store_erase',0xf800,1024)
    else:p.call(0x2f0c,'syscon_cfg_store_append',0xf800,1024,KEY,VALUE)
    compare_controllers(p)
    assert not p.original.hook_calls and not p.candidate.hook_calls


def test_runtime_load_parser_clamping_and_invalid_persistent_values(config_elf):
    p=controller_pair(config_elf)
    # Obtain recovered key strings from the original readonly data, not guessed names.
    pointers=[0xb036,0xb044,0xb058,0xb06f,0xb084,0xb095,0xb0ac,0xb0ba]
    names=[string(p.original,a) for a in pointers]
    for value in [b'',b'true',b'false',b'1',b'0',b'2',b'-1',b'30',b'31',b'2147483648',b'9999999999999999999999',b'3tail',b'TRUE']:
        flash=bytearray(b'\xff'*1024)
        for index,name in enumerate(names):flash[index*64:(index+1)*64]=slot(name,value)
        p.put(0xfc00,flash);p.put(0xf800,slot(b'hw_revision',b'123456789')+b'\xff'*960)
        # Trigger genuine load through the assigned identity append entry.
        p.put(KEY,b'x\0');p.put(VALUE,b'y\0');p.call(0x3278,'syscon_cfg_identity_append',KEY,VALUE)
        compare_controllers(p)
    assert not p.original.hook_calls and not p.candidate.hook_calls


def test_writable_character_domain_and_erase_size_rounding(config_elf):
    p=controller_pair(config_elf)
    for c in range(256):
        for position in [0,29,30,31]:
            p.put(KEY,b'a'*position+bytes([c])+b'\0'+b'\xa5'*8)
            p.call(0x2810,'syscon_cfg_field_writable',KEY)
    for size in [0,1,63,64,65,127,128,960,1024]:
        p.put(0xf800,bytes(2048))
        p.call(0x27a8,'syscon_cfg_store_erase',0xf800,size)
        compare_controllers(p)
    assert not p.original.hook_calls and not p.candidate.hook_calls


def test_mutable_controller_backing_rejects_cpu_stores_and_original_execution(config_elf):
    from unicorn import UcError,UC_ERR_FETCH_PROT
    p=controller_pair(config_elf)
    # Peripheral mem_write is the only allowed mutation mechanism: a real ARM
    # store is detected even though the backing mapping is writable for the
    # controller model. This negative control must fail the test environment.
    with pytest.raises(AssertionError,match='CPU wrote flash outside FLASHCTL'):
        p.candidate.call('syscon_rt_memset',0xf800,0,1)
    p=controller_pair(config_elf)
    with pytest.raises(UcError) as fault:p.candidate.call(0xf800)
    assert fault.value.errno==UC_ERR_FETCH_PROT
