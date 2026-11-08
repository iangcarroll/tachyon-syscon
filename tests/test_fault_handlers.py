import json
import struct
import subprocess
from pathlib import Path
import pytest
from unicorn.arm_const import UC_ARM_REG_LR,UC_ARM_REG_PC,UC_ARM_REG_SP
from mspm0_core_oracle import MSPM0CoreOracle

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def fault_images(tmp_path_factory):
    root=tmp_path_factory.mktemp('fault-arm')
    obj=root/'fault.o'
    subprocess.run(['arm-none-eabi-gcc','-std=c11','-Wall','-Wextra','-Werror',
        '-mcpu=cortex-m0plus','-mthumb','-Os','-ffreestanding','-ffunction-sections',
        '-fno-unwind-tables','-fno-asynchronous-unwind-tables','-c',
        str(ROOT/'src/drivers/fault_handlers.c'),'-o',str(obj)],check=True)
    images={}
    for name in ('default_exception','hardfault','nmi'):
        elf=root/(name+'.elf');binary=root/(name+'.bin')
        symbol='syscon_'+name
        subprocess.run(['arm-none-eabi-ld','--gc-sections','-e',symbol,'-Ttext=0x10000',str(obj),'-o',str(elf)],check=True)
        subprocess.run(['arm-none-eabi-objcopy','-O','binary',str(elf),str(binary)],check=True)
        symbols=subprocess.check_output(['arm-none-eabi-nm',str(elf)],text=True)
        entry=next(int(line.split()[0],16) for line in symbols.splitlines() if line.split()[-1]==symbol)
        images[name]=(binary.read_bytes(),entry)
    return images


@pytest.mark.parametrize('name,original',[
    ('default_exception',0x79e4),('hardfault',0x7bb8),('nmi',0x7bcc)])
def test_cortex_m0_fault_code_matches_original_write_and_never_returns(fault_images,name,original):
    initial={0x400b040c:0x93675a21}
    reference=MSPM0CoreOracle(initial)
    reference.hooks.pop(original,None)
    candidate=MSPM0CoreOracle(initial)
    image,entry=fault_images[name]
    candidate.put(0x10000,image)
    for cpu,start in ((reference,original),(candidate,entry)):
        cpu.cpu.reg_write(UC_ARM_REG_SP,0x20000ff0)
        cpu.cpu.reg_write(UC_ARM_REG_LR,0x100f1)
        cpu.cpu.emu_start(start|1,0x100f0,count=100)
        pc=cpu.cpu.reg_read(UC_ARM_REG_PC)
        assert pc!=0x100f0
        before=list(cpu.trace)
        cpu.cpu.emu_start(pc|1,0x100f0,count=100)
        assert cpu.cpu.reg_read(UC_ARM_REG_PC)==pc
        assert cpu.trace==before
    assert candidate.trace==reference.trace
    assert candidate.registers==reference.registers
