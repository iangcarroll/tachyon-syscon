"""Flash effects and return values compared with executed original Thumb code."""
import ctypes as C
import random
import pytest
from config_oracle import ConfigOracle, FlashModel, FirmwareAssertion

BLANK=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_size_t)
PROGRAM=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_size_t,C.c_void_p)
ERASE=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_size_t)
FAULT=C.CFUNCTYPE(None,C.c_void_p)

class IO(C.Structure):
    _fields_=[('context',C.c_void_p),('blank',BLANK),('program',PROGRAM),('erase',ERASE),('fault',FAULT)]

class Store(C.Structure):
    _fields_=[('slots',C.c_void_p),('count',C.c_size_t),('io',IO)]

class NativeStore:
    def __init__(self,lib,initial=None,count=15,fail=None):
        self.lib=lib
        self.memory=C.create_string_buffer(bytes(initial) if initial is not None else b'\xff'*1024,1024)
        addr=C.addressof(self.memory)
        self.flash=FlashModel(lambda off,n:C.string_at(addr+off,n),lambda off,data:C.memmove(addr+off,data,len(data)),fail)
        self.faults=0
        def fault(_): self.faults+=1
        self.callbacks=(BLANK(lambda _,off:self.flash.operation('blank',off)),
                        PROGRAM(lambda _,off,data:self.flash.operation('program',off,C.string_at(data,8))),
                        ERASE(lambda _,off:self.flash.operation('erase',off)),FAULT(fault))
        self.store=Store(addr,count,IO(None,*self.callbacks))
        for name in ['append','compact']:
            getattr(lib,'syscon_store_'+name).argtypes=[C.POINTER(Store),C.c_char_p,C.c_char_p]
        lib.syscon_config_set.argtypes=[C.POINTER(Store),C.c_char_p,C.c_char_p]
        lib.syscon_store_get.argtypes=[C.POINTER(Store),C.c_char_p,C.c_void_p]
        lib.syscon_store_erase.argtypes=[C.POINTER(Store)]
        lib.syscon_store_init.argtypes=[C.POINTER(Store)]
        lib.syscon_config_load.argtypes=[C.POINTER(Store),C.POINTER(Store),C.c_void_p]

    def invoke(self,op,key=b'',value=b''):
        if op=='get':
            out=C.create_string_buffer(b'\x5a'*32,32)
            result=self.lib.syscon_store_get(C.byref(self.store),key,out)
            return result,out.raw
        if op=='set':return self.lib.syscon_config_set(C.byref(self.store),key,value)
        fn=getattr(self.lib,'syscon_store_'+op)
        if op in ['erase','init']:return fn(C.byref(self.store))
        return fn(C.byref(self.store),key,value)

    def contents(self):return self.memory.raw


def slot(lib,key,value):
    b=C.create_string_buffer(64)
    assert lib.syscon_slot_encode(b,key,value)==1
    return b.raw

def image(lib,entries,tail=b'\xff'*64):
    b=bytearray(b'\xff'*960+tail)
    for i,key,value in entries:b[i*64:(i+1)*64]=slot(lib,key,value)
    return bytes(b)

def compare(o,n,op,key=b'',value=b''):
    expected=o.invoke(op,key,value)
    actual=n.invoke(op,key,value)
    assert actual==expected,(op,key,value,actual,expected)
    assert n.contents()==o.contents(),(op,key,value)
    assert n.flash.events==o.flash.events,(op,key,value)


def test_append_full_erase_and_reinitialize(lib):
    for count,base in [(15,0xfc00),(16,0xf800)]:
        o=ConfigOracle(base=base,count=count);n=NativeStore(lib,count=count)
        compare(o,n,'init')
        for i in range(18):compare(o,n,'append',b'duplicate',str(i).encode())
        compare(o,n,'init')
        compare(o,n,'erase')
        compare(o,n,'init')


def test_update_compaction_randomized_sequences(lib):
    rng=random.Random(0x2abc)
    for keys in [3,7,8,9,12]:
        o=ConfigOracle();n=NativeStore(lib)
        compare(o,n,'init')
        for i in range(120):
            key=f'key{rng.randrange(keys)}'.encode()
            value=rng.choice([b'',b'true',b'false',b'1',b'0',f'value{i}'.encode()])
            compare(o,n,'set',key,value)
            compare(o,n,'get',key)


def test_compaction_corruption_and_sector_tail(lib):
    rng=random.Random(0xc0ffee)
    for run in range(60):
        initial=bytearray(image(lib,[(i,f'k{rng.randrange(7)}'.encode(),f'v{i}'.encode()) for i in range(15)],tail=rng.randbytes(64)))
        for _ in range(rng.randrange(6)):
            i=rng.randrange(15);kind=rng.randrange(4)
            if kind==0:initial[i*64+63]^=1
            elif kind==1:initial[i*64+31]^=1
            elif kind==2:
                initial[i*64:i*64+64]=b'\xff'*64
                initial[i*64+60]=0  # Not an unused slot, despite empty key.
            else:
                # Legacy delimiter-containing key/value with valid checksums.
                initial[i*64:i*64+64]=slot(lib,b'old',b'abc')
                initial[i*64+1]=ord(';')
                initial[i*64+33]=ord(';')
                for off in [i*64,i*64+32]:
                    check=0
                    for b in initial[off:off+31]:check^=b
                    initial[off+31]=check
        o=ConfigOracle(initial);n=NativeStore(lib,initial)
        compare(o,n,'compact',b'new',b'value')


@pytest.mark.parametrize('kind,steps',[('blank',range(1,10)),('program',range(1,66)),('erase',range(1,17))])
def test_compaction_failures_preserve_partial_effects(lib,kind,steps):
    initial=image(lib,[(i,f'k{i%6}'.encode(),f'value{i}'.encode()) for i in range(15)],tail=b'\xa5'*64)
    for step in steps:
        o=ConfigOracle(initial,fail=(kind,step));n=NativeStore(lib,initial,fail=(kind,step))
        compare(o,n,'set',b'new',b'value')


def test_init_faults_and_presence_not_version(lib):
    for value in [b'2',b'',b'old']:
        initial=image(lib,[(3,b'confVersion',value)])
        o=ConfigOracle(initial);n=NativeStore(lib,initial)
        compare(o,n,'init')
        assert not o.flash.events
    for failure in [('erase',1),('program',1),('program',5),('blank',1)]:
        o=ConfigOracle(fail=failure);n=NativeStore(lib,fail=failure)
        try: expected=o.invoke('init')
        except FirmwareAssertion: expected=-1
        assert n.invoke('init')==expected
        assert n.contents()==o.contents()
        assert n.flash.events==o.flash.events
        assert n.faults==int(expected==-1)


def test_invalid_arguments_and_empty_key_assertion(lib):
    for key,value in [(b'x',b'bad value'),(b'x',b'a;b'),(b'x'*31,b'v'),(b'k',b'x'*31),(b'x',b''),(b'',b'x')]:
        o=ConfigOracle();n=NativeStore(lib)
        try: expected=o.invoke('set',key,value)
        except FirmwareAssertion: expected=-1
        assert n.invoke('set',key,value)==expected
        assert n.contents()==o.contents()
        assert n.flash.events==o.flash.events


def test_runtime_load_original_packed_abi(lib):
    rng=random.Random(0x2df8)
    keys=[b'sys.auto_boot',b'sys.wake_pin_enable',b'sys.color_debug_enable',b'sys.fastboot_enabled',b'sys.demo_enabled',b'sys.enable_5v_when_off']
    numbers=[b'-1',b'-0',b'0',b'2',b'3',b'29',b'30',b'31',b'2147483647',b'2147483648',b'999999999999999999999999999999',b'123x',b'']
    for iteration in range(100):
        entries=[(i,k,rng.choice([b'true',b'false',b'1',b'0',b'TRUE',b'unknown',b''])) for i,k in enumerate(keys)]
        entries += [(6,b'sys.edl_timer',rng.choice(numbers)),(7,b'sys.shutdown_timer',rng.choice(numbers))]
        initial=image(lib,entries)
        ident=image(lib,[(0,b'hw_revision',rng.choice([b'1.2',b'1.3',b'01234567890',b'']))])
        o=ConfigOracle(initial);o.put(0xf800,ident)
        n=NativeStore(lib,initial);identity=NativeStore(lib,ident,count=16)
        packed=C.create_string_buffer(22)
        lib.syscon_config_load(C.byref(n.store),C.byref(identity.store),packed)
        assert packed.raw==o.invoke('load'),entries
