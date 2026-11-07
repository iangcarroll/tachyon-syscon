import ctypes as C
import random
import struct
import pytest
from flash_controller_oracle import FlashControllerModel,FlashControllerOracle,ConfigControllerOracle
from test_config_updates import NativeStore,Store,IO,BLANK,PROGRAM,ERASE,FAULT,image
from config_oracle import FirmwareAssertion

READ=C.CFUNCTYPE(C.c_uint32,C.c_void_p,C.c_uint32)
WRITE=C.CFUNCTYPE(None,C.c_void_p,C.c_uint32,C.c_uint32)
REPORT=C.CFUNCTYPE(None,C.c_void_p,C.c_uint,C.c_char_p,C.c_char_p)
class ControllerIO(C.Structure):
    _fields_=[('context',C.c_void_p),('read',READ),('write',WRITE)]


def controller_io(lib,model):
    io=ControllerIO(None,READ(lambda _,address:model.read(address)),WRITE(lambda _,address,value:model.write(address,value)))
    lib.syscon_flash_execute.argtypes=[C.c_void_p,C.c_uint32]
    lib.syscon_flash_erase.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32]
    lib.syscon_flash_program.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_void_p]
    lib.syscon_flash_blank.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32]
    return io


class Pair:
    def __init__(self,lib,busy=(4,4,0),fail=None):
        self.lib=lib
        self.original=FlashControllerOracle(busy,fail)
        self.flash=bytearray(self.original.cpu.mem_read(0,65536))
        self.model=FlashControllerModel(lambda address,n:bytes(self.flash[address:address+n]),
            lambda address,data:self.flash.__setitem__(slice(address,address+len(data)),data),busy,fail)
        self.io=controller_io(lib,self.model)

    def check(self):
        assert self.model.trace==self.original.controller.trace
        assert self.model.events==self.original.controller.events
        assert self.model.registers==self.original.controller.registers
        assert self.flash==self.original.cpu.mem_read(0,65536)

    def unprotect(self):
        self.original.call(0x7b44,self.model.BASE)
        self.lib.syscon_flash_unprotect_main(C.byref(self.io),self.model.BASE)
        self.check()

    def program(self,address,data):
        self.original.put(0x20000900,data)
        expected=self.original.call(0x7b10,self.model.BASE,address,0x20000900)
        actual=self.lib.syscon_flash_program(C.byref(self.io),self.model.BASE,address,C.c_char_p(data))
        assert actual==expected
        self.check()
        return actual

    def blank(self,address):
        expected=self.original.call(0x7b60,self.model.BASE,address)
        actual=self.lib.syscon_flash_blank(C.byref(self.io),self.model.BASE,address)
        assert actual==expected
        self.check()
        return actual

    def erase(self,address,size=0x40):
        expected=self.original.call(0x7af4,self.model.BASE,address,size)
        actual=self.lib.syscon_flash_erase(C.byref(self.io),self.model.BASE,address,size)
        assert actual==expected
        self.check()
        return actual


def test_flash_command_transactions_protection_and_busy_statuses(lib):
    p=Pair(lib,busy=(0,2,4,5,6,7,0xfffffff4))
    assert p.program(0xfc00,b'12345678')==1
    assert p.erase(0xfc40)==1
    p.unprotect()
    assert p.model.registers[p.model.BASE+0x1210]==0xffffffff
    assert p.blank(0xfc00)==3
    assert p.program(0xfc00,b'12345678')==3
    assert p.blank(0xfc00)==1
    assert p.program(0xfc00,b'\xff'*8)==1
    assert p.erase(0xfc40)==3
    assert p.blank(0xfc00)==3


def test_flash_write_setup_cannot_mutate_before_execute_and_completion(lib):
    p=Pair(lib)
    p.unprotect()
    m=p.model
    before=bytes(p.flash)
    for offset,value in [(0x1104,1),(0x1124,255),(0x1120,0xfc00),(0x1130,0),(0x1134,0)]:m.write(m.BASE+offset,value)
    assert p.flash==before
    m.write(m.BASE+0x1100,0)
    assert p.flash==before
    m.write(m.BASE+0x1100,1)
    assert p.flash==before
    for _ in m.busy:
        m.read(m.BASE+0x13d0)
        assert p.flash==before
    assert m.read(m.BASE+0x13d0)==3
    assert p.flash[0xfc00:0xfc08]==b'\0'*8


@pytest.mark.parametrize('failure',[('erase',1),('program',2),('blank',2)])
def test_flash_injected_terminal_errors_and_recovery(lib,failure):
    p=Pair(lib,busy=(4,)*50,fail=failure)
    p.unprotect()
    for _ in range(3):
        p.erase(0xfc00)
        p.blank(0xfc00)
        p.program(0xfc00,b'\0'*8)


def test_flash_model_rejects_unsupported_addresses_and_sizes(lib):
    p=Pair(lib)
    p.unprotect()
    for address in [0xfc01,0x10000,0x41c00000,0xffffffff]:
        assert p.program(address,b'\0'*8)==1
        assert p.blank(address)==1
    for size in [0,0x10,0x50,0xffffffff]:assert p.erase(0xfc00,size)==1


class NativeControllerStore(NativeStore):
    def __init__(self,lib,initial=None,base=0xfc00,count=15,busy=(4,4,0),fail=None):
        super().__init__(lib,initial,count)
        pointer=C.addressof(self.memory)
        self.controller=FlashControllerModel(lambda address,n:C.string_at(pointer+address-base,n),
                                             lambda address,data:C.memmove(pointer+address-base,data,len(data)),busy,fail)
        self.controller_io=controller_io(lib,self.controller)
        self.diagnostics=[]
        self.report=REPORT(lambda _,level,tag,msg:self.diagnostics.append((level,tag,msg)))
        def operation(kind,offset,data=None):
            lib.syscon_flash_unprotect_main(C.byref(self.controller_io),self.controller.BASE)
            address=base+offset
            if kind=='blank':result=lib.syscon_flash_blank(C.byref(self.controller_io),self.controller.BASE,address)
            elif kind=='program':result=lib.syscon_flash_program(C.byref(self.controller_io),self.controller.BASE,address,data)
            else:result=lib.syscon_flash_erase(C.byref(self.controller_io),self.controller.BASE,address,0x40)
            if result!=3:lib.syscon_flash_report(C.byref(self.controller_io),self.controller.BASE,self.report,None)
            return result
        def fault(_):self.faults+=1
        self.callbacks=(BLANK(lambda _,off:operation('blank',off)),
                        PROGRAM(lambda _,off,data:operation('program',off,data)),
                        ERASE(lambda _,off:operation('erase',off)),FAULT(fault))
        self.store.io=IO(None,*self.callbacks)


def test_config_algorithms_through_real_flashctl_and_ram_executor(lib):
    rng=random.Random(0x7af4)
    for fail in [None,('blank',3),('program',10),('erase',3)]:
        initial=image(lib,[(i,f'k{i%4}'.encode(),str(i).encode()) for i in range(15)],tail=b'\xa5'*64)
        o=ConfigControllerOracle(initial,busy=(4,0,6),fail=fail)
        n=NativeControllerStore(lib,initial,busy=(4,0,6),fail=fail)
        for index in range(25):
            key=f'k{rng.randrange(5)}'.encode();value=str(index).encode()
            expected=o.invoke('set',key,value)
            actual=n.invoke('set',key,value)
            assert actual==expected
            assert n.contents()==o.contents()
            assert n.controller.trace==o.controller.trace
            assert n.controller.events==o.controller.events
            assert n.controller.registers==o.controller.registers
            assert n.diagnostics==o.controller_diagnostics
        # At least one flash command executed its original copied-RAM routine.
        assert 0x20000008 in o.executed and 0x2000000e in o.executed


def test_flash_status_diagnostics_preserve_legacy_mask_and_combination_behavior(lib):
    p=Pair(lib)
    original=[];native=[]
    def log(o):original.append((o.arg(0),o.cstring(o.arg(1)),o.cstring(o.arg(2))))
    p.original.hooks[0x8f88]=log
    callback=REPORT(lambda _,level,tag,msg:native.append((level,tag,msg)))
    rng=random.Random(0x2738)
    statuses=[((i&15)<<4)|((i&16)<<4)|((i&32)<<7) for i in range(64)]
    statuses += [rng.getrandbits(32) for _ in range(100)]
    for status in statuses:
        p.model.registers[p.model.BASE+0x13d0]=status
        p.original.controller.registers[p.model.BASE+0x13d0]=status
        p.original.call(0x2738)
        lib.syscon_flash_report(C.byref(p.io),p.model.BASE,callback,None)
        assert native==original
        p.check()
