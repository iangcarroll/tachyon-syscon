import json
import struct
from pathlib import Path
import pytest
from emulate import from_scenario,send_command,report
from inventory import ROOT,load_image
from mspm0.core import UnsupportedRegister,MissingImage

SCENARIO=ROOT/'fixtures/emulator/tachyon-synthetic.json'

def boot():
    m,scenario=from_scenario(SCENARIO)
    assert m.run(1000000,until=0x3c9a)==('breakpoint',0x3c9a)
    return m,scenario

def test_reset_through_application_flash_executor_interrupts_and_version_command():
    m,scenario=boot();original=load_image()
    assert set([0x79f0,0x96d4,0x3b34,0x20000000])<=m.executed
    assert m.flash[:0xf800]==original.ljust(65536,b'\xff')[:0xf800]
    assert m.flash[0xf800:0xfc00]!=b'\xff'*1024 and m.flash[0xfc00:0xffc0]!=b'\xff'*960
    assert any(e[:2]==('exception-enter',15) for e in m.events)
    before=len(m.events);output=send_command(m,'VERSION')
    version=original[0xf7f8:].split(b'\0')[0]
    assert b'Version='+version+b'\r\n' in output and b'PASS\r\n' in output
    assert any(e[:2]==('exception-enter',31) for e in m.events[before:])
    assert any(e[:2]==('exception-return',31) for e in m.events[before:])
    evidence=report(m,scenario,original)
    assert evidence['original_function_hooks']==[] and evidence['application_loop_reached']
    assert evidence['copied_sram_executor_executed'] and not evidence['physical_hardware_accessed']

def test_config_set_get_persists_through_fresh_cpu_boot():
    m,_=boot();prefix=bytes(m.flash[:0xf800])
    assert b'PASS\r\n' in send_command(m,'CONFIG_SET emu.key alpha')
    assert b'alpha' in send_command(m,'CONFIG_GET emu.key')
    n,_=from_scenario(SCENARIO,bytes(m.flash))
    assert n.run(1000000,until=0x3c9a)[0]=='breakpoint'
    output=send_command(n,'CONFIG_GET emu.key')
    assert b'alpha' in output and b'PASS\r\n' in output
    assert bytes(n.flash[:0xf800])==prefix

def test_missing_factory_data_and_unspecified_writeonly_reads_stop_without_defaults(tmp_path):
    scenario=json.loads(SCENARIO.read_text());scenario.pop('factory_fill')
    path=tmp_path/'missing-factory.json';path.write_text(json.dumps(scenario))
    m,_=from_scenario(path)
    # Application boot need not touch factory calibration on every path. An
    # explicit CPU read must still fault instead of receiving fabricated bytes.
    assert m.run(1000000,until=0x3c9a)[0]=='breakpoint'
    m.write_ram(0x20000c00,b'\x00\x48\x00\x68'+struct.pack('<I',0x41c4003c))
    m.cpu.reg_write(11,0x20000c01)
    with pytest.raises(MissingImage):m.run(2)
    scenario=json.loads(SCENARIO.read_text());scenario['writeonly_read_fixtures']={}
    path.write_text(json.dumps(scenario));m,_=from_scenario(path)
    with pytest.raises(UnsupportedRegister,match='write-only'):m.run(1000000)

def test_expander_nack_negative_control_changes_real_firmware_fault_path():
    baseline,_=boot();normal=bytes(baseline.device.tx[0])
    broken,_=from_scenario(SCENARIO);broken.device.expander.failures.extend(['nack']*4)
    broken.run(1500000)
    abnormal=bytes(broken.device.tx[0])
    assert abnormal!=normal
    assert any(token in abnormal.lower() for token in (b'failed',b'error',b'assert',b'fault'))
    assert broken.device.expander.events!=baseline.device.expander.events
