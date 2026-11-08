"""Editable source and linker layout exercised through full MCU sessions."""
import json
import subprocess
import shutil
import sys

import pytest

import build_runtime_scan_image as runtime
from build_physical_firmware import elf_audit,emit_binary
from inventory import load_image
from rebuilt_system import boot,command_reply,compare,normalized_log,candidate_stack_floor
from test_config_helpers import slot
from test_rebuilt_system import legacy_compaction


@pytest.fixture(scope='module')
def relocated_image(tmp_path_factory):
    tmp_path=tmp_path_factory.mktemp('firmware-relocation')
    # Build a real source variant in isolation, including its own linker script.
    # No current-tree edits, guest patches, reused binary or function stubs.
    tree=tmp_path/'source'
    for directory in ('src','include','target','vendor','tools'):
        shutil.copytree(runtime.ROOT/directory,tree/directory,
                        ignore=shutil.ignore_patterns('__pycache__'))
    header=tree/'include/config_text.h'
    header.write_text(header.read_text().replace('Key checksum mismatch',
                      'Configuration key checksum mismatch (longer editable text)'))
    linker=tree/'target/physical/firmware.ld'
    script=linker.read_text()
    assert script.count('.config_data :')==1
    script=script.replace('.config_data :','.config_data ORIGIN(SPARE)+256 :')
    assert script.count('.text_early : {')==1 and script.count('.text : {')==1
    script=script.replace('.text_early : {','.text_early : { . += 16;')
    script=script.replace('.text : {','.text : { . += 32;')
    assert script.count('.data : ALIGN(4) {')==1
    script=script.replace('.data : ALIGN(4) {','.data ORIGIN(RAM_AUX)+64 : ALIGN(4) {')
    needle='__ram_exec_start = .; KEEP(*(.ram_original_flash))'
    assert script.count(needle)==1
    script=script.replace(needle,'__ram_exec_start = .; '+4*'SHORT(0xde00); '+'KEEP(*(.ram_original_flash))')
    # Exercise linker allocation within reclaimed SRAM with a different object
    # order. No production code knows either object's resulting address.
    order='*(.bss.syscon_timer_state) *(.bss.syscon_task_state)'
    assert script.count(order)==1
    script=script.replace(order,'*(.bss.syscon_task_state) *(.bss.syscon_timer_state)')
    linker.write_text(script)
    output=tmp_path/'physical'
    subprocess.run([sys.executable,str(tree/'tools/build_physical_firmware.py'),
                    '--output',str(output)],check=True,capture_output=True,text=True)
    manifest=json.loads((output/'manifest.json').read_text())
    assert manifest['status']=='linked-experimental'
    assert manifest['inputs_unchanged_during_build']
    assert not manifest['layout_audit']['issues']
    section=manifest['layout_audit']['sections']['.config_data']
    assert section['address']==0xe578+256 and section['flags']==2
    assert section['address']+section['bytes']<=0xf7f8
    cache=manifest['layout_audit']['symbols']['syscon_config_state']
    data=manifest['layout_audit']['sections']['.data']
    assert data['address']<=cache<data['address']+data['bytes']
    assert cache>=0x20000820+64
    return output,manifest,script


def test_relocated_reset_uart_and_fresh_boot_persistence(relocated_image):
    output,manifest,_=relocated_image
    assert candidate_stack_floor(output/'firmware.bin')==manifest['layout_audit']['stack_floor_address']
    result=compare((output/'firmware.bin').read_bytes(),stack_floor=manifest['layout_audit']['stack_floor_address'])
    assert result['persistent_flash_equal']
    assert all(session['equal_after_timestamp_normalization'] for session in result['sessions'])
    assert not result['firmware_function_replacements']
    assert result['rebuilt']['minimum_msp_during_session']>=manifest['layout_audit']['symbols']['__extra_bss_end']



def test_relocated_globals_button_battery_curve_and_compaction(relocated_image):
    output,manifest,_=relocated_image
    # Exercise the actual cache consumers through UART after moving SRAM and
    # poisoning the old cache. No handler replacement or guest code patching.
    floor=manifest['layout_audit']['stack_floor_address']
    machines=[boot(load_image())[0],boot((output/'firmware.bin').read_bytes(),stack_floor=floor)[0]]
    poison=b'\xa5'*22
    machines[1].cpu.mem_write(0x20000030,poison)
    # The former task/timer region now holds the linker-allocated state arena;
    # it is live memory, so only genuinely vacant locations are poisoned.
    obsolete=[(0x200000da,3),
              (0x200000b4,36),(0x200000d8,2),(0x20000390,24),
              (0x200000f4,72),(0x20000685,11),(0x20000694,1)]
    for address,size in obsolete:machines[1].write_ram(address,b'\xa5'*size)
    ticks=manifest['layout_audit']['symbols']['syscon_timer_state']+104
    clock_before=int.from_bytes(machines[1].read(ticks,8),'little')
    for command in ['CONFIG_INTERNAL','CONFIG_SET sys.edl_timer 17','CONFIG_INTERNAL']:
        replies=[command_reply(machine,command) for machine in machines]
        assert all(b'PASS\r\n' in reply for reply in replies)
        assert normalized_log(replies[0])==normalized_log(replies[1])
    assert b'sys.edl_timer: 17' in replies[1]
    assert bytes(machines[1].cpu.mem_read(0x20000030,len(poison)))==poison
    assert machines[0].flash[0xf800:]==machines[1].flash[0xf800:]
    assert int.from_bytes(machines[1].read(ticks,8),'little')>clock_before
    for address,size in obsolete:assert machines[1].read(address,size)==b'\xa5'*size

    # GPIO edges reach the real interrupt, debounce timer and application queue
    # after both code and button data move. No handler is replaced or invoked
    # directly. The accelerated external clock is synthetic, not cycle timing.
    from power_key_session import exercise_short_press
    original_button=exercise_short_press(machines[0],0x3a8c)
    rebuilt_button=exercise_short_press(machines[1],
        manifest['layout_audit']['symbols']['syscon_target_queue_event'])
    assert original_button==rebuilt_button
    for address,size in obsolete:assert machines[1].read(address,size)==b'\xa5'*size
    assert machines[1].minimum_msp>=manifest['layout_audit']['symbols']['__extra_bss_end']

    # Battery ADC input rises and falls while the real UART report repeatedly
    # traverses the relocated channel table and scale state. Check both the
    # oracle and independent progression; equal stuck output is not sufficient.
    import re
    battery_mv=[]
    for sample in (2200,2300,3100,2300,2200):
        for machine in machines:machine.device.adc_inputs[2]=sample
        replies=[command_reply(machine,'READ_PWR') for machine in machines]
        assert all(b'PASS\r\n' in reply for reply in replies)
        assert normalized_log(replies[0])==normalized_log(replies[1])
        match=re.search(rb'\[MFGD\] VBAT: : (\d+)mV\r\n',replies[1])
        assert match,replies[1]
        battery_mv.append(int(match[1]))
    assert battery_mv[0]<battery_mv[1]<battery_mv[2]
    assert battery_mv[3:]==[battery_mv[1],battery_mv[0]]
    for address,size in obsolete:assert machines[1].read(address,size)==b'\xa5'*size

    # Legacy values must also remain literal after recompilation moves code,
    # constants and SRAM. No reserved byte at a private return address is needed.
    literal=b"%s/%u/%n"
    persisted,value,_=legacy_compaction((output/'firmware.bin').read_bytes(),literal,machines,stack_floor=floor)
    assert value==literal
    assert persisted[64:128]==bytes(slot(b'legacy',literal))


def test_stack_guard_rejects_unreclaimed_storage_during_compaction(relocated_image,tmp_path):
    output,manifest,script=relocated_image
    # Reproduce the actual migration defect: allocate a second scheduler copy
    # above the old state instead of reclaiming its now-unused SRAM. Firmware
    # source, callbacks, emulator behavior and input values remain unchanged.
    for section in ('syscon_retained_state','syscon_timer_state','syscon_task_state'):
        pattern='*(.bss.'+section+')'
        assert script.count(pattern)==1
        script=script.replace(pattern,'')
    linker=tmp_path/'unreclaimed.ld';linker.write_text(script)
    elf=tmp_path/'unreclaimed.elf'
    objects=[str(p) for p in output.glob('*.o') if p.name!='physical-inputs.o']
    subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',
                    *objects,'-Wl,--gc-sections','-Wl,-T,'+str(linker),
                    '-o',str(elf)],check=True,capture_output=True,text=True)
    audit=elf_audit(elf)
    assert not audit['issues']  # A successful link alone did not catch this bug.
    floor=audit['stack_floor_address']
    assert floor>manifest['layout_audit']['stack_floor_address']
    binary=tmp_path/'unreclaimed.bin';emit_binary(elf,binary)
    engines=[]
    with pytest.raises(AssertionError,match='Stack overlaps allocated state'):
        legacy_compaction(binary.read_bytes(),b'%s/%u/%n',engines,stack_floor=floor)
    assert engines  # Startup succeeded; the collision occurs during compaction.
    assert b'Config storage full, attempting compaction' in bytes(engines[0].device.tx[0])


def test_stack_bound_rejects_a_manifest_for_different_firmware(relocated_image,tmp_path):
    output,_,_=relocated_image
    image=bytearray((output/'firmware.bin').read_bytes());image[-1]^=1
    (tmp_path/'firmware.bin').write_bytes(image)
    shutil.copyfile(output/'manifest.json',tmp_path/'manifest.json')
    with pytest.raises(ValueError,match='does not match the layout manifest'):
        candidate_stack_floor(tmp_path/'firmware.bin')
