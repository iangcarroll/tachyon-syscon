"""Whole-image SYSRESETREQ restores retained PMU values after C startup."""
from pathlib import Path
import pytest
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_LR

from build_physical_firmware import build
from inventory import load_image
from rebuilt_system import boot,command_reply,normalized_log

@pytest.fixture(scope='module')
def physical(tmp_path_factory):
    out=tmp_path_factory.mktemp('warm-reset-physical')
    manifest=build(out)
    assert manifest['status']=='linked-experimental'
    return (out/'firmware.bin').read_bytes(),manifest['layout_audit']['symbols']

@pytest.mark.parametrize('retained',[(0x5b,0x10,9),(0x5b,0x20,254),(0x22,0x10,17)])
def test_warm_reset_restores_retained_state_after_data_initialization(physical,retained):
    candidate,symbols=physical
    observations=[]
    for image,load_entry,cache,retained_address in [(load_image(),0x59d8,0x20000030,0x200000da),
                                   (candidate,symbols['syscon_target_retained_load']&~1,symbols['syscon_config_state'],symbols['syscon_retained_state'])]:
        m,_=boot(image)
        for i,value in enumerate(retained):m.write_register(0x400b0400+4*i,value)
        # Warm reset preserves physical SRAM, but startup intentionally reloads
        # normal data. The retained SRAM mirror must come from PMU, not these bytes.
        m.write_ram(retained_address,b'\xa5'*3)
        m.write_ram(cache,b'\xa5'*22)
        button_blocks=([(0x200000b4,36),(0x200000d8,2),(0x20000390,24)]
                       if image==load_image() else
                       [(symbols['syscon_powerkey_ranges'],36),
                        (symbols['syscon_powerkey_control'],2),
                        (symbols['syscon_powerkey_runtime'],24)])
        for address,size in button_blocks:m.write_ram(address,b'\xa5'*size)
        reset_count=m.reset_count
        loaded=[];return_pc=None;loop=False
        def writes(cpu,kind,address,size,value,unused):
            nonlocal loop
            if m.reset_count==reset_count+1 and address==0x400b040c and value==2:loop=True
        def code(cpu,address,size,unused):
            nonlocal return_pc
            if m.reset_count!=reset_count+1:return
            if address==load_entry:return_pc=cpu.reg_read(UC_ARM_REG_LR)&~1
            elif address==return_pc and not loaded:
                loaded.append((bytes(m.read(retained_address,3)),
                               tuple(m.read_register(0x400b0400+4*i) for i in range(3)),
                               bytes(m.read(cache,22)),
                               tuple(m.read(address,size) for address,size in button_blocks)))
            if loop:cpu.emu_stop()
        hooks=[m.cpu.hook_add(UC_HOOK_MEM_WRITE,writes),m.cpu.hook_add(UC_HOOK_CODE,code)]
        m.write_register(0xe000ed0c,0x05fa0004)
        m.run(2000000)
        for hook in hooks:m.cpu.hook_del(hook)
        assert m.reset_count==reset_count+1 and loop and len(loaded)==1
        expected=retained if retained[0]==0x5b else (0x5b,0,0)
        assert loaded[0][0]==bytes(expected) and loaded[0][1]==expected
        # The original reset copies the same configuration defaults on warm boot.
        assert loaded[0][2]!=b'\xa5'*22
        reply=command_reply(m,'VERSION')
        assert b'Version=1.0.52\r\n' in reply and b'PASS\r\n' in reply
        observations.append((loaded,bytes(m.read(retained_address,3)),
                             tuple(m.read_register(0x400b0400+4*i) for i in range(3)),
                             normalized_log(reply),bytes(m.flash[0xf800:])))
    assert observations[0]==observations[1]
