"""RGB target ABI, soft-float bit patterns, aliasing and state/read/write order."""
import random
import struct
import pytest
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UC_MEM_READ
from unicorn.arm_const import UC_ARM_REG_R1
from arm_rebuild_oracle import ArmRebuildOracle
from oracle import Oracle
from rgb_target_oracle import build,MAPPINGS,DEPENDENCIES
R=0x200003a8

@pytest.fixture(scope='module')
def rgb_target_elf(tmp_path_factory):return build(tmp_path_factory.mktemp('rgb-target'))

def string(cpu,address):
    text=bytearray()
    for i in range(256):
        byte=cpu.cpu.mem_read(address+i,1)
        if byte==b'\0':return bytes(text)
        text.extend(byte)
    raise AssertionError('Unterminated RGB text')


class Pair:
    def __init__(self,elf):
        self.cpus=[Oracle(),ArmRebuildOracle(elf)];self.events=[[],[]];self.memory=[[],[]]
        self.responses={};self.mutate=None
        for i,cpu in enumerate(self.cpus):
            for addr,(name,count) in DEPENDENCIES.items():
                entry=addr if i==0 else cpu.symbols['syscon_target_'+name]&~1
                def call(machine,i=i,name=name,count=count):
                    args=tuple(machine.arg(j) for j in range(count))
                    if name=='timer_register':
                        expected=0x5cad if i==0 else machine.symbols['syscon_target_rgb_tick']|1
                        assert args[2]==expected;args=(*args[:2],'relocated:rgb_tick',args[3])
                    if name=='logger':args=(args[0],string(machine,args[1]),string(machine,args[2]),args[3])
                    self.events[i].append((name,args))
                    if self.mutate:self.mutate(machine,i,name,args)
                    return self.responses.get(name,0)
                cpu.hooks[entry]=call
            def trace(uc,kind,address,size,value,_,i=i):
                if kind==UC_MEM_READ:value=int.from_bytes(uc.mem_read(address,size),'little')
                self.memory[i].append((kind,address,size,value&((1<<(size*8))-1)))
            cpu.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,trace,begin=R,end=R+27)
    def put(self,address,data):
        for cpu in self.cpus:cpu.put(address,data)
    def call(self,address,*args):
        self.events=[[],[]];self.memory=[[],[]]
        left=self.cpus[0].call(address,*args,count=1000000)
        right=self.cpus[1].call('syscon_target_rgb_'+MAPPINGS[address],*args,count=1000000)
        if address in (0x5df4,0x5e0c):
            assert string(self.cpus[0],left)==string(self.cpus[1],right)
        elif address not in [0x5b48,0x5e24]:
            assert left==right,(hex(address),args,left,right)
        if address==0x5cac:assert self.cpus[0].cpu.reg_read(UC_ARM_REG_R1)==self.cpus[1].cpu.reg_read(UC_ARM_REG_R1)
        assert self.events[0]==self.events[1],(hex(address),self.events)
        assert self.memory[0]==self.memory[1],(hex(address),self.memory)
        assert bytes(self.cpus[0].cpu.mem_read(R,28))==self.cpus[1].read(R,28)
        return left


def test_rgb_init_retains_tail_bytes_and_registers_source_callback(rgb_target_elf):
    p=Pair(rgb_target_elf);rng=random.Random(0x5b7c)
    for active in [0,1,255,256,0xffffffff]:
        for result in [0,1,0xffffffff,0x80000000]:
            p.put(R,rng.randbytes(28));p.responses['timer_register']=result;p.call(0x5b7c,active)


def test_rgb_scaling_all_float_classes_and_unsigned_channel_wrap(rgb_target_elf):
    p=Pair(rgb_target_elf);rng=random.Random(0x5b20)
    bits=[0,0x80000000,1,0x80000001,0x7fffff,0x800000,0x7f800000,0xff800000,
          0x7fc00000,0xffc12345,0x7f800001,0x3f800000,0x42c80000,0xbf800000,
          0x4effffff,0x4f000000,0x4f800000]+[rng.getrandbits(32) for _ in range(150)]
    for value in bits:
        for active in [0,1]:
            p.put(R+8,struct.pack('<I',value));p.put(R+16,bytes([active]))
            p.call(0x5b20,rng.getrandbits(32))


def test_rgb_configuration_aliases_and_callback_changes(rgb_target_elf):
    p=Pair(rgb_target_elf);rng=random.Random(0x5c38)
    for config in [0,0x20000800,*range(R,R+24)]:
        p.put(R,rng.randbytes(28));p.put(0x20000800,bytes([12,34,56,78,2]))
        p.call(0x5c38,config)
    def mutate(cpu,i,name,args):
        if name=='pwm_write':cpu.put(R+2,bytes([(args[0]*77)&255]))
    p.mutate=mutate;p.call(0x5b48)


def test_rgb_pattern_brightness_preset_names_and_config_output_aliases(rgb_target_elf):
    p=Pair(rgb_target_elf);rng=random.Random(0x5bfc)
    for value in [0,1,2,3,4,5,9,10,100,101,255,256,0xffffffff]:
        for flush in [0,1]:
            p.put(R,rng.randbytes(28));p.call(0x5bd4,value,flush)
            p.call(0x5bfc,value,flush)
        p.call(0x5c68,value,rng.getrandbits(32));p.call(0x5df4,value);p.call(0x5e0c,value)
    for out in [0,0x20000800,*range(R,R+23)]:
        p.put(R,rng.randbytes(28));p.call(0x5dc8,out)
        if out:assert bytes(p.cpus[0].cpu.mem_read(out,6))==p.cpus[1].read(out,6)
    p.call(0x5dbc);p.call(0x5e24)


def test_rgb_tick_every_pattern_with_raw_float_bits_and_duration_expiry(rgb_target_elf):
    p=Pair(rgb_target_elf);rng=random.Random(0x5cac)
    for pattern in [0,1,2,3,4,5,6,255]:
        for level in [0,0x80000000,0x7f800000,0xff800000,0x7fc00000,0x7f800001,0x3f800000,0x42c80000,*[rng.getrandbits(32) for _ in range(12)]]:
            for duration in [0,1,2]:
                state=bytearray(rng.randbytes(28));state[0]=pattern;state[22]=rng.randrange(12)
                struct.pack_into('<I',state,8,level);struct.pack_into('<I',state,24,duration)
                p.put(R,state);p.call(0x5cac,rng.getrandbits(32),rng.getrandbits(32))


def test_rgb_animation_long_sequence_and_transient_restore(rgb_target_elf):
    p=Pair(rgb_target_elf)
    for pattern in range(1,6):
        p.call(0x5b7c,0);p.put(0x20000800,bytes([255,31,63,100,pattern]));p.call(0x5c38,0x20000800)
        for index in range(220):p.call(0x5cac,index,0x12345678)
    for preset in range(10):
        p.call(0x5c68,preset,0);p.call(0x5e24)
        p.call(0x5cac,123,456);p.call(0x5cac,123,456)
        assert p.call(0x5dbc)==preset


def test_rgb_has_no_dependency_on_original_tables_or_strings(rgb_target_elf):
    p=Pair(rgb_target_elf)
    p.cpus[1].put(0xce05,b'\xa5'*(0xcf68-0xce05))
    p.cpus[1].put(0xd776,b'\xa5'*4)
    p.cpus[1].put(0xdaa5,b'\xa5'*8)
    p.responses['timer_register']=0xffffffff
    p.call(0x5b7c,0)
    for preset in range(10):
        p.call(0x5c68,preset,0)
        p.call(0x5df4,preset)
        for _ in range(6):p.call(0x5cac,0,0)
    for pattern in range(7):p.call(0x5e0c,pattern)
    p.call(0x5df4,255)


def test_editing_a_preset_changes_behavior_without_address_changes(tmp_path,monkeypatch):
    import build_arm_test_image as runtime
    header=(runtime.ROOT/'include/rgb_data.h').read_text()
    old='[SYSCON_RGB_FACTORY]   = {255, 255, 255,  30, SYSCON_RGB_BLINKING}'
    new='[SYSCON_RGB_FACTORY]   = {255, 255, 255,  73, SYSCON_RGB_BLINKING}'
    assert header.count(old)==1
    shadow=tmp_path/'include';shadow.mkdir()
    (shadow/'rgb_data.h').write_text(header.replace(old,new))
    monkeypatch.setattr(runtime,'FLAGS',[*runtime.FLAGS,'-I'+str(shadow)])
    p=Pair(build(tmp_path/'variant'))
    p.cpus[0].call(0x5b7c,1)
    p.cpus[1].call('syscon_target_rgb_init',1)
    p.events=[[],[]]
    p.cpus[0].call(0x5c68,3,0)
    p.cpus[1].call('syscon_target_rgb_preset',3,0)
    writes=[[args for name,args in events if name=='pwm_write'] for events in p.events]
    assert [port for port,value in writes[0]]==[port for port,value in writes[1]]
    assert len(writes[0])==len(writes[1])==3
    assert all(after[1]>before[1] for before,after in zip(writes[0],writes[1]))
    assert (runtime.ROOT/'include/rgb_data.h').read_text()==header
