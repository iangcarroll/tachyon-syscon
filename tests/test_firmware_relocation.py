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
    assert script.count('.peripheral_data : ALIGN(4) {')==1
    script=script.replace('.peripheral_data : ALIGN(4) {',
                          '.peripheral_data ORIGIN(RAM_PERIPHERALS)+8 : ALIGN(4) {')
    assert script.count('.irq_bss (NOLOAD) : {')==1
    script=script.replace('.irq_bss (NOLOAD) : {',
                          '.irq_bss ORIGIN(RAM_IRQ_STATE)+8 (NOLOAD) : {')
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


def vacant_ranges(manifest,ranges):
    """Subtract live linker allocations before poisoning obsolete locations."""
    segments=[(address,address+size) for address,size in ranges]
    for section in manifest['layout_audit']['sections'].values():
        start=section['address'];end=start+section['bytes']
        if not 0x20000000<=start<0x20001000 or start==end:continue
        remaining=[]
        for low,high in segments:
            if high<=start or low>=end:remaining.append((low,high));continue
            if low<start:remaining.append((low,start))
            if high>end:remaining.append((end,high))
        segments=remaining
    return [(low,high-low) for low,high in segments if low<high]


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
    symbols=manifest['layout_audit']['symbols']
    for name,old in [('syscon_gpio_pins',0x2000016c),
                     ('syscon_gpio_handlers',0x20000698),
                     ('syscon_reset_cause_cache',0x20000254),
                     ('syscon_i2c_bus',0x2000013c),('syscon_i2c_state',0x20000760)]:
        assert symbols[name]!=old
    # A writer/reader pair retaining the same old callback address could still
    # agree with itself. Require registration in the actual relocated object.
    registered=int.from_bytes(machines[1].read(symbols['syscon_gpio_handlers'],4),'little')
    assert registered==symbols['syscon_target_powerkey_edge']
    poison=b'\xa5'*22
    machines[1].cpu.mem_write(0x20000030,poison)
    # The former task/timer region now holds the linker-allocated state arena;
    # it is live memory, so only genuinely vacant locations are poisoned.
    obsolete=[(0x200000da,3),
              (0x200000b4,36),(0x200000d8,2),(0x20000390,24),
              (0x20000685,11),(0x20000694,1)]
    # The old ADC table now holds relocated LED/PWM objects. Poison only the
    # unallocated prefix; a stale ADC lookup would instead encounter LED data.
    peripheral_start=manifest['layout_audit']['sections']['.peripheral_data']['address']
    obsolete.append((0x200000f4,peripheral_start-0x200000f4))
    obsolete+= [(0x2000013c,12),(0x2000016c,200),(0x20000254,1),
                (0x20000698,200),(0x20000760,2)]
    obsolete=vacant_ranges(manifest,obsolete)
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


@pytest.mark.parametrize('objects_to_duplicate',[
    ['.bss.syscon_retained_state','.bss.syscon_timer_state','.bss.syscon_task_state'],
    ['.data.syscon_pwm_channels','.bss.syscon_rgb_runtime'],
],ids=['scheduler','led'])
def test_stack_guard_rejects_unreclaimed_storage_during_compaction(relocated_image,tmp_path,objects_to_duplicate):
    output,manifest,script=relocated_image
    # Reproduce the actual migration defect: allocate a second state copy
    # above the old state instead of reclaiming its now-unused SRAM. Firmware
    # source, callbacks, emulator behavior and input values remain unchanged.
    for section in objects_to_duplicate:
        pattern='*('+section+')'
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


def test_relocated_rgb_animation_reaches_pwm_outputs(relocated_image):
    """UART -> RGB state -> timer IRQ -> three real timer compare registers."""
    from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
    from unicorn.arm_const import UC_ARM_REG_R0
    output,manifest,_=relocated_image
    machines=[boot(load_image())[0],
              boot((output/'firmware.bin').read_bytes(),
                   stack_floor=manifest['layout_audit']['stack_floor_address'])[0]]
    obsolete=[(0x20000148,36),(0x200003a8,28)]
    obsolete=vacant_ranges(manifest,obsolete)
    for address,size in obsolete:machines[1].write_ram(address,b'\xa5'*size)
    entries=[0x5c38,manifest['layout_audit']['symbols']['syscon_target_rgb_configure']&~1]
    # Observe output values, not instruction timestamps. The external tick
    # advance is synthetic, while firmware handlers and callbacks run normally.
    ports=(0x40085814,0x40085810,0x40089814)  # red, green, blue
    results=[]
    for machine,entry in zip(machines,entries):
        armed=False
        writes=[]
        def code(cpu,address,size,unused):
            nonlocal armed
            if address==entry:
                argument=cpu.reg_read(UC_ARM_REG_R0)
                if bytes(cpu.mem_read(argument,5))==bytes([12,34,56,78,1]):
                    armed=True
        def memory(cpu,kind,address,size,value,unused):
            if armed and address in ports and len(writes)<24:
                assert size==4
                writes.append((address,value))
        hooks=[machine.cpu.hook_add(UC_HOOK_CODE,code),
               machine.cpu.hook_add(UC_HOOK_MEM_WRITE,memory)]
        try:
            reply=command_reply(machine,'SET_RGB 12:34:56:78:1:')
            assert b'PASS\r\n' in reply
            for _ in range(200):
                if len(writes)==24:break
                machine.advance(machine.systick_load+1)
                machine.run(2000)
        finally:
            for hook in hooks:machine.cpu.hook_del(hook)
        assert armed and len(writes)==24,writes
        assert [address for address,value in writes]==list(ports)*8
        frames=[tuple(value for address,value in writes[i:i+3]) for i in range(0,24,3)]
        assert len(set(frames))>1,frames  # Equal but stuck images must fail.
        status=command_reply(machine,'LEDSTATUS')
        assert b'breathing' in status and b'PASS\r\n' in status
        results.append((writes,normalized_log(reply),normalized_log(status)))
    assert results[0]==results[1]
    for address,size in obsolete:assert machines[1].read(address,size)==b'\xa5'*size


def test_relocated_i2c_nack_runs_real_fault_path(relocated_image,tmp_path):
    from rebuilt_system import SCENARIO
    from unicorn.arm_const import UC_ARM_REG_PRIMASK
    output,manifest,_=relocated_image
    inputs=json.loads(SCENARIO.read_text());inputs['i2c_failures']=['nack']*4
    scenario=tmp_path/'i2c-nack.json';scenario.write_text(json.dumps(inputs))
    machines=[];outputs=[]
    for image,floor in [(load_image(),0x20000820),
                         ((output/'firmware.bin').read_bytes(),manifest['layout_audit']['stack_floor_address'])]:
        with pytest.raises(AssertionError,match='Reset did not reach application loop'):
            boot(image,scenario,budget=1000000,observer=machines.append,stack_floor=floor)
        machine=machines[-1]
        wire=normalized_log(bytes(machine.device.tx[0]))
        assert b'Assertion failed:' in wire
        assert machine.cpu.reg_read(UC_ARM_REG_PRIMASK)==1
        assert not machine.systick_ctrl&2
        assert machine.device.expander.events
        outputs.append(wire)
    assert outputs[0]==outputs[1]


def test_relocated_uart_stream_uses_linked_receive_ring(relocated_image):
    output,manifest,_=relocated_image
    symbols=manifest['layout_audit']['symbols']
    for name,old in [('syscon_uart_ports',0x20000234),
                     ('syscon_uart_config',0x20000762),('syscon_uart_rings',0x20000774)]:
        assert symbols[name]!=old
    machines=[boot(load_image())[0],
              boot((output/'firmware.bin').read_bytes(),
                   stack_floor=manifest['layout_audit']['stack_floor_address'])[0]]
    obsolete=vacant_ranges(manifest,[(0x20000234,32),(0x20000762,18),(0x20000774,152)])
    for address,size in obsolete:machines[1].write_ram(address,b'\xa5'*size)
    rings=[0x20000774,symbols['syscon_uart_rings']]
    before=[machine.read(address+64,8) for machine,address in zip(machines,rings)]
    # Enough real command input to wrap the 64-byte ring. Compare replies and
    # actual linked indices, so paired stale writer/reader addresses cannot pass.
    for command in ['VERSION','CONFIG_SET uart.edit relocatable',
                    'CONFIG_GET uart.edit','VERSION','CONFIG_GET uart.edit']:
        replies=[command_reply(machine,command) for machine in machines]
        assert all(b'PASS\r\n' in reply for reply in replies)
        assert normalized_log(replies[0])==normalized_log(replies[1])
        indices=[machine.read(address+64,8) for machine,address in zip(machines,rings)]
        assert indices[0]==indices[1]
    assert b'uart.edit = relocatable' in replies[1]
    assert all(previous!=current for previous,current in zip(before,indices))
    for address,size in obsolete:assert machines[1].read(address,size)==b'\xa5'*size


def test_relocated_logger_enable_disable_and_real_command_registers(relocated_image):
    output,manifest,_=relocated_image
    symbol=manifest['layout_audit']['symbols']['syscon_log_enabled']
    assert symbol!=0x2000080c
    machines=[boot(load_image())[0],
              boot((output/'firmware.bin').read_bytes(),
                   stack_floor=manifest['layout_audit']['stack_floor_address'])[0]]
    machines[1].write_ram(0x2000080c,b'\xa5')
    flags=[0x2000080c,symbol]
    traces=[]
    for machine,flag in zip(machines,flags):
        before=len(machine.device.tx[0])
        # LOG 0 cannot use command_reply: the status logger is disabled before
        # the handler returns. Feed real UART bytes and check continued polling.
        for value in b'LOG 0\n':
            machine.device.inject_uart(0,bytes([value]));machine.run(5000)
        deadline=machine.instructions+2_000_000
        while machine.read(flag,1)!=b'\0' and machine.instructions<deadline:
            machine.run(10000)
        assert machine.read(flag,1)==b'\0'
        muted=len(machine.device.tx[0])
        for value in b'VERSION\n':
            machine.device.inject_uart(0,bytes([value]));machine.run(5000)
        machine.run(20000)
        reply=command_reply(machine,'LOG 1')
        assert b'PASS\r\n' in reply and machine.read(flag,1)==b'\1'
        # UART echo is independent of logger enable. The muted VERSION must
        # finish before LOG 1 by FIFO order, without its formatted response.
        assert b'Version=' not in bytes(machine.device.tx[0][muted:])
        assert b'Version=1.0.52\r\n' in command_reply(machine,'VERSION')
        # Preserve the real logger -> UART caller-register behavior used by
        # the legacy SET_RGB parser, while its private return addresses move.
        for token in ['0','%u','%s','%p','%d','%x','%c','%3u']:
            assert b'PASS\r\n' in command_reply(machine,f'SET_RGB {token}:2:3:4:0:')
        traces.append(normalized_log(bytes(machine.device.tx[0][before:])))
    assert traces[0]==traces[1]
    assert machines[1].read(0x2000080c,1)==b'\xa5'
