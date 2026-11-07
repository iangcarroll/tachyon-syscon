"""Standalone target callback entries, including self-aliasing output contexts."""
import random
import struct
import subprocess
from pathlib import Path
import pytest
from unicorn import UC_MEM_READ,UC_MEM_WRITE,UC_HOOK_MEM_READ,UC_HOOK_MEM_WRITE,UcError,UC_PROT_READ,UC_PROT_EXEC
from unicorn.arm_const import UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11
from arm_rebuild_oracle import ArmRebuildOracle
from oracle import Oracle

ROOT=Path(__file__).resolve().parents[1]
CTX=0x20000800
DEST=0x20000900
CALLEE=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]

@pytest.fixture(scope='module')
def callback_elf(tmp_path_factory):
    elf=tmp_path_factory.mktemp('callback-helpers')/'test.elf'
    subprocess.run(['arm-none-eabi-gcc','-std=c11','-Os','-mcpu=cortex-m0plus','-mthumb',
        '-ffreestanding','-fno-builtin','-nostdlib','-Wall','-Wextra','-Werror',
        '-I',str(ROOT/'include'),str(ROOT/'target/callback_helpers.c'),
        '-Wl,-T,'+str(ROOT/'target/emulation.ld'),'-Wl,-e,syscon_target_buffer_output',
        '-o',str(elf)],check=True)
    return elf


def test_buffer_callback_order_aliasing_unsigned_limits_and_full_character_return(callback_elf):
    o=Oracle();a=ArmRebuildOracle(callback_elf);rng=random.Random(0x9012)
    events=[[],[]]
    def record(index):
        def hook(uc,kind,address,size,value,_):
            if CTX<=address<0x20000c00:
                events[index].append((kind,address,size,(value & ((1 << (size*8))-1)) if kind==UC_MEM_WRITE else bytes(uc.mem_read(address,size))))
        return hook
    for i,machine in enumerate((o,a)):
        machine.cpu.hook_add(UC_HOOK_MEM_READ|UC_HOOK_MEM_WRITE,record(i))
    cases=[(u,c) for u in (0,1,255,0x7fffffff,0xfffffffe,0xffffffff)
                 for c in (0,1,256,0x80000000,0xffffffff)]
    cases += [(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(100)]
    for used,capacity in cases:
        # Force even very large indices into accessible memory via ARM32 wrap.
        for destination in (DEST,*range(CTX,CTX+12)):
            value=rng.getrandbits(32);data=rng.randbytes(1024)
            context=struct.pack('<III',(destination-used)&0xffffffff,capacity,used)
            saved=[rng.getrandbits(32) for _ in CALLEE]
            for machine in (o,a):
                machine.put(CTX,data);machine.put(CTX,context)
                for register,initial in zip(CALLEE,saved):machine.cpu.reg_write(register,initial)
            events[0].clear();events[1].clear()
            assert o.call(0x9012,value,CTX)==a.call('syscon_target_buffer_output',value,CTX)==value
            assert bytes(o.cpu.mem_read(CTX,1024))==a.read(CTX,1024)
            assert events[0]==events[1]
            for machine in (o,a):assert [machine.cpu.reg_read(r) for r in CALLEE]==saved


def test_buffer_full_does_not_read_or_follow_destination(callback_elf):
    o=Oracle();a=ArmRebuildOracle(callback_elf)
    # Context begins eight bytes before SRAM: the buffer word is unmapped,
    # while capacity and used reside in actual SRAM. Full means no buffer read.
    context=0x1ffffffc
    for machine in (o,a):machine.put(0x20000000,struct.pack('<II',0,0xffffffff))
    assert o.call(0x9012,0xabcdef00,context)==a.call('syscon_target_buffer_output',0xabcdef00,context)


def test_buffer_fault_keeps_preceding_counter_write_and_no_output_validation(callback_elf):
    for destination in (0x30000000,0x20001000,0x40000000,0x40):
        o=Oracle();a=ArmRebuildOracle(callback_elf)
        o.cpu.mem_protect(0,0x10000,UC_PROT_READ|UC_PROT_EXEC)
        for machine in (o,a):machine.put(CTX,struct.pack('<III',destination,1,0))
        for machine,entry in ((o,0x9012),(a,'syscon_target_buffer_output')):
            with pytest.raises(UcError):machine.call(entry,0xaabbccdd,CTX)
            assert machine.u32(CTX+8)==1


def test_failure_callback_order_pointer_identity_return_and_preserved_registers(callback_elf):
    rng=random.Random(0x3f08)
    for command in (0,CTX,0xffffffff):
        o=Oracle();a=ArmRebuildOracle(callback_elf);events=[[],[]]
        returns=[rng.getrandbits(32) for _ in range(3)]
        def sink(index):
            def callback(machine):
                events[index].append(machine.arg(0))
                # Only caller-saved state is changed by an AAPCS callback.
                return returns[len(events[index])-1]
            return callback
        original_callback=0x10040;o.hooks[original_callback]=sink(0)
        replacement_callback=a.callback(sink(1))
        saved=[rng.getrandbits(32) for _ in CALLEE]
        for machine in (o,a):
            for register,initial in zip(CALLEE,saved):machine.cpu.reg_write(register,initial)
        reason=rng.getrandbits(32)
        actual=o.call(0x3f08,command,reason,original_callback|1)
        rebuilt=a.call('syscon_target_failure',command,reason,replacement_callback)
        assert actual==rebuilt==returns[len(events[0])-1]
        assert events[0]==events[1]==([command] if command else [])+[reason,0xb6c6]
        for machine in (o,a):assert [machine.cpu.reg_read(r) for r in CALLEE]==saved


def test_null_callback_preserves_character_without_dereferencing_context(callback_elf):
    o=Oracle();a=ArmRebuildOracle(callback_elf);rng=random.Random(0x9026)
    for _ in range(500):
        character,context=rng.getrandbits(32),rng.getrandbits(32)
        before=a.state()
        assert o.call(0x9026,character,context)==a.call('syscon_target_null_output',character,context)==character
        assert a.state()==before
