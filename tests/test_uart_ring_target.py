"""Source-linked UART interfaces retain original ring layout and MMIO order."""
import random
import struct
import subprocess
from collections import defaultdict,deque
from pathlib import Path
import pytest
from unicorn import UC_MEM_READ,UC_MEM_WRITE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UcError
from arm_rebuild_oracle import ArmRebuildOracle
from oracle import Oracle
from power_state_comparison import PowerStateComparison

ROOT=Path(__file__).resolve().parents[1]
BASES=[0x40108000,0x40100000]
RING=0x20000774
DISABLED=0x2000076a

class AssertReached(RuntimeError):pass

@pytest.fixture(scope='module')
def uart_elf(tmp_path_factory):
    return build_uart_ring(tmp_path_factory.mktemp('uart-ring-target'))


def build_uart_ring(out,include=ROOT/'include',linker=ROOT/'target/emulation.ld'):
    elf=out/'test.elf'
    trap=out/'assert.c';trap.write_text('void syscon_target_assert(unsigned a,unsigned b,unsigned c){(void)a;(void)b;(void)c;__asm__("bkpt #0");}\n')
    subprocess.run(['arm-none-eabi-gcc','-std=c11','-Os','-mcpu=cortex-m0plus','-mthumb',
        '-ffreestanding','-fno-builtin','-nostdlib','-Wall','-Wextra','-Werror',
        '-I',str(include),str(ROOT/'target/uart_ring.c'),str(ROOT/'target/uart_state.c'),str(ROOT/'target/uart_ring_abi.S'),str(ROOT/'target/hal_helpers.c'),
        str(ROOT/'src/runtime_memory.c'),str(trap),'-Wl,-T,'+str(linker),
        '-Wl,-e,syscon_target_uart_read','-o',str(elf)],check=True)
    return elf


def test_edited_ring_capacity_changes_real_irq_buffering_without_offset_edits(tmp_path):
    import shutil
    include=tmp_path/'include';shutil.copytree(ROOT/'include',include)
    header=include/'uart_state.h';original=header.read_text()
    assert original.count('SYSCON_UART_RX_CAPACITY = 64')==1
    header.write_text(original.replace('SYSCON_UART_RX_CAPACITY = 64',
                                       'SYSCON_UART_RX_CAPACITY = 128'))
    # Isolated test SRAM has room for the intentional size change. A physical
    # build still has to satisfy the MCU's independent RAM/stack constraints.
    linker=tmp_path/'edited.ld';script=(ROOT/'target/emulation.ld').read_text()
    old='TEST_UART_RINGS (rw) : ORIGIN = 0x20000774, LENGTH = 152'
    assert script.count(old)==1
    linker.write_text(script.replace(old,'TEST_UART_RINGS (rw) : ORIGIN = 0x21000000, LENGTH = 280'))
    machine=ArmRebuildOracle(build_uart_ring(tmp_path,include,linker))
    for base in BASES:machine.cpu.mem_map(base,0x2000)
    def inject(value):
        machine.put(BASES[0]+0x1020,struct.pack('<I',11))
        machine.put(BASES[0]+0x1124,struct.pack('<I',value))
        machine.call('syscon_target_uart_irq',BASES[0])
    for value in range(160):inject(value)
    assert machine.call('syscon_target_uart_available',0)==128
    assert [machine.call('syscon_target_uart_read',0) for _ in range(128)]==list(range(128))
    assert machine.call('syscon_target_uart_read',0)==0xffffffff
    for value in range(255,223,-1):inject(value)
    assert [machine.call('syscon_target_uart_read',0) for _ in range(32)]==list(range(255,223,-1))
    assert (ROOT/'include/uart_state.h').read_text()==original

class Pair:
    def __init__(self,elf):
        self.o=Oracle();self.a=ArmRebuildOracle(elf);self.events=[[],[]];self.scripts=[defaultdict(deque),defaultdict(deque)];self.assertions=[[],[]]
        self.power_state=PowerStateComparison(self.o,self.a)
        for i,machine in enumerate((self.o,self.a)):
            for base in BASES:machine.cpu.mem_map(base,0x2000)
            machine.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,self.record(i))
            def trap(cpu,index=i):
                self.assertions[index].append((cpu.cstring(cpu.arg(0)),cpu.arg(1),cpu.cstring(cpu.arg(2))))
                raise AssertReached()
            address=0x2678 if i==0 else self.a.symbols['syscon_target_assert']&~1
            machine.hooks[address]=trap
    def record(self,index):
        def hook(cpu,kind,address,size,value,_):
            if not (0x20000000<=address<0x20000c00 or any(base<=address<base+0x2000 for base in BASES)):return
            if kind==UC_MEM_READ and self.scripts[index][address]:
                value=self.scripts[index][address].popleft();cpu.mem_write(address,value.to_bytes(size,'little'))
            self.events[index].append((kind,address,size,(value & ((1 << (size*8))-1)) if kind==UC_MEM_WRITE else bytes(cpu.mem_read(address,size))))
        return hook
    def put(self,address,data):
        for machine in (self.o,self.a):machine.put(address,data)
    def word(self,address,value):self.put(address,struct.pack('<I',value&0xffffffff))
    def script(self,address,values):
        for s in self.scripts:s[address]=deque(values)
    def call(self,entry,name,*args,returns=True):
        for events in self.events:events.clear()
        left=self.o.call(entry,*args);right=self.a.call('syscon_target_uart_'+name,*args)
        if returns:assert left==right,(hex(entry),args,left,right)
        assert self.events[0]==self.events[1],(hex(entry),args,self.events)
        assert bytes(self.o.cpu.mem_read(0x20000000,0xc00))==self.power_state.memory(0x20000000,self.a.read(0x20000000,0xc00))
        return left


def test_uart_available_preserves_unsigned_ring_counts_full_flags_and_mask_order(uart_elf):
    p=Pair(uart_elf);rng=random.Random(0x8cf0)
    cases=[(0,0),(63,0),(0,63),(0xffffffff,0),(0,0xffffffff),(0x7fffffff,0),(0x80000000,0)]
    cases += [(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(50)]
    for port in range(2):
        for write,read in cases:
            for full,disabled in [(0,0),(1,0),(255,0),(0,1),(0,255)]:
                p.word(RING+port*76+64,write);p.word(RING+port*76+68,read)
                p.put(RING+port*76+72,bytes([full]));p.put(DISABLED+port*9,bytes([disabled]))
                p.word(BASES[port]+0x1028,rng.getrandbits(32))
                p.call(0x8cf0,'available',port)


def test_uart_receive_irq_and_read_roundtrip_with_real_ring_and_low_level_helpers(uart_elf):
    p=Pair(uart_elf);rng=random.Random(0x8d70)
    for port in range(2):
        p.put(DISABLED+port*9,b'\0');p.put(RING+port*76,bytes(76))
        expected=deque()
        for _ in range(300):
            if rng.randrange(3):
                value=rng.getrandbits(32);p.word(BASES[port]+0x1020,0xab00|11);p.word(BASES[port]+0x1124,value)
                p.call(0x8d70,'irq',BASES[port],returns=False)
                if len(expected)<64:expected.append(value&255)
            else:
                value=p.call(0x8de4,'read',port)
                assert value==(expected.popleft() if expected else 0xffffffff)
            assert p.call(0x8cf0,'available',port)==len(expected)
        while expected:assert p.call(0x8de4,'read',port)==expected.popleft()


def test_uart_irq_aliasing_ring_indices_descriptor_priority_and_disabled_state(uart_elf):
    rng=random.Random(0x8dc2)
    for write in [0,63,64,65,68,72,75,0xffffffff]:
        for disabled in (0,1):
            p=Pair(uart_elf);p.put(RING,rng.randbytes(76));p.word(RING+64,write);p.word(RING+68,(write+2)&0xffffffff);p.put(RING+72,b'\0')
            p.put(DISABLED,bytes([disabled]));p.word(BASES[0]+0x1020,11);p.word(BASES[0]+0x1124,rng.getrandbits(32))
            p.call(0x8d70,'irq',BASES[0],returns=False)
    # With identical descriptor bases the second descriptor selects port 1.
    p=Pair(uart_elf);p.word(0x20000244+8,BASES[0]);p.put(RING,bytes(152));p.put(DISABLED+9,b'\0')
    p.word(BASES[0]+0x1020,11);p.word(BASES[0]+0x1124,0x5a)
    p.call(0x8d70,'irq',BASES[0],returns=False)
    assert p.o.u32(RING+76+64)==1 and p.o.u32(RING+64)==0
    p.call(0x8d70,'irq',0x30000000,returns=False)
    for iidx in (0,1,10,12,0xffffff00):
        p.word(BASES[0]+0x1020,iidx);p.call(0x8d70,'irq',BASES[0],returns=False)


def test_uart_read_arbitrary_accessible_indices_signed_count_and_reloads(uart_elf):
    rng=random.Random(0x8e44)
    for port in range(2):
        for read in (0,1,63,64,68,72,100,0xffffffff):
            p=Pair(uart_elf);p.put(RING,rng.randbytes(300));p.put(DISABLED+port*9,b'\0')
            ring=RING+port*76;p.word(ring+64,(read+1)&0xffffffff);p.word(ring+68,read);p.put(ring+72,b'\0')
            p.call(0x8de4,'read',port)
        p=Pair(uart_elf);p.put(DISABLED+port*9,b'\0');p.word(RING+port*76+64,0x80000000);p.word(RING+port*76+68,0);p.put(RING+port*76+72,b'\0')
        assert p.call(0x8de4,'read',port)==0xffffffff


def test_uart_tx_waits_full_words_buffer_bytes_and_disabled_dereference_suppression(uart_elf):
    p=Pair(uart_elf);rng=random.Random(0x8c34)
    for port in range(2):
        p.put(DISABLED+port*9,b'\0')
        for size in (0,1,31,127):
            data=rng.randbytes(size);p.put(0x20000a00,data)
            p.script(BASES[port]+0x1108,[0x80,0x80,0]*size)
            p.call(0x8c8c,'write_buffer',port,0x20000a00,size)
            values=[e[3] for e in p.events[0] if e[0]==UC_MEM_WRITE and e[1]==BASES[port]+0x1120]
            assert bytes(values)==data
        for _ in range(30):
            value=rng.getrandbits(32);p.script(BASES[port]+0x1108,[0x80,0])
            assert p.call(0x8c34,'put',port,value)==0
            assert p.o.u32(BASES[port]+0x1120)==value
        p.put(DISABLED+port*9,b'\xff')
        p.call(0x8c8c,'write_buffer',port,0x30000000,0xffffffff)
        p.call(0x8c34,'put',port,0xffffffff)
        p.put(DISABLED+port*9,b'\0');p.call(0x8c8c,'write_buffer',port,0x30000000,0)


def test_uart_invalid_ports_reach_original_assertion_with_same_source_location(uart_elf):
    for port in (2,3,255,0xffffffff):
        for entry,name,args in [(0x8c34,'put',(port,42)),(0x8c8c,'write_buffer',(port,0,0)),(0x8cf0,'available',(port,)),(0x8de4,'read',(port,))]:
            p=Pair(uart_elf)
            for machine,address in ((p.o,entry),(p.a,'syscon_target_uart_'+name)):
                with pytest.raises(AssertReached):machine.call(address,*args)
            assert p.assertions[0]==p.assertions[1]
            assert p.assertions[0][0][0]==b'hal_uart.cpp'


def test_uart_ring_assertions_ignore_original_private_rom(uart_elf):
    p=Pair(uart_elf)
    p.a.put(0xe0af,b'\xa5'*(0xe0ef-0xe0af))
    p.a.put(0xcfb8,b'\xa5'*16)
    for machine,entry in [(p.o,0x8de4),(p.a,'syscon_target_uart_read')]:
        with pytest.raises(AssertReached):machine.call(entry,2)
    assert p.assertions[0]==p.assertions[1]


def test_uart_buffer_faults_after_same_transmitted_prefix(uart_elf):
    p=Pair(uart_elf);p.put(DISABLED,b'\0');p.put(0x20000ffe,b'AB')
    # Place data at top SRAM but keep calls' stacks in separate mapped harness
    # RAM so the original prologue cannot overwrite these test input bytes.
    for machine in (p.o,p.a):machine.cpu.mem_map(0x22000000,4096)
    from unicorn.arm_const import UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2
    for machine,entry in ((p.o,0x8c8c),(p.a,p.a.symbols['syscon_target_uart_write_buffer'])):
        machine.cpu.reg_write(UC_ARM_REG_SP,0x22000f00);machine.cpu.reg_write(UC_ARM_REG_LR,machine.SENTINEL|1)
        for register,value in zip((UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2),(0,0x20000ffe,4)):machine.cpu.reg_write(register,value)
        with pytest.raises(UcError):machine.cpu.emu_start(entry|1,machine.SENTINEL,count=10000)
    outputs=[[e[3] for e in events if e[0]==UC_MEM_WRITE and e[1]==BASES[0]+0x1120] for events in p.events]
    assert outputs[0]==outputs[1]==list(b'AB')


def test_uart_buffer_preserves_original_all_return_registers_and_exposed_frame(uart_elf):
    from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_SP
    regs=(UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)
    for port in (0,1):
        for disabled in (0,1,255):
            for size in (0,1,7,64):
                p=Pair(uart_elf);p.put(DISABLED+port*9,bytes([disabled]));p.put(0x20000a00,bytes(range(64)))
                p.call(0x8c8c,'write_buffer',port,0x20000a00,size)
                left=tuple(p.o.cpu.reg_read(r) for r in regs);right=tuple(p.a.cpu.reg_read(r) for r in regs)
                assert left==right==(0,port,size,size)
    # Transmit bytes aliasing the original exposed32-byte UART entry frame.
    # Both executables run with identical SP, incoming registers and LR.
    from unicorn.arm_const import UC_ARM_REG_LR,UC_ARM_REG_PC
    p=Pair(uart_elf);sp=0x20000f00
    for m,entry in ((p.o,0x8c8c),(p.a,p.a.symbols['syscon_target_uart_write_buffer'])):
        m.cpu.mem_map(0x22000000,4096)
        m.cpu.reg_write(UC_ARM_REG_SP,sp);m.cpu.reg_write(UC_ARM_REG_LR,0x22000001)
        for r,v in zip(regs,(0,sp-32,12,0x12345678)):m.cpu.reg_write(r,v)
        m.cpu.emu_start(entry|1,0x22000000,count=10000)
        assert m.cpu.reg_read(UC_ARM_REG_PC)==0x22000000
    assert p.events[0]==p.events[1]
