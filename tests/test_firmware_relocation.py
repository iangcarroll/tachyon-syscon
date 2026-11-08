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
    compaction=tree/'target/config/config_update.c'
    text=compaction.read_text()
    declaration='    char kept[8][2][31], candidate[31];'
    assert text.count(declaration)==1
    text=text.replace(declaration,declaration+'\n    volatile uint8_t edit_workspace[96] = {0};')
    completion='    syscon_target_logger(3, CONF, SYSCON_CFG_COMPACT_COMPLETE, count);'
    assert text.count(completion)==1
    text=text.replace(completion,completion+'\n    __asm__ volatile("" : "+m"(edit_workspace) : : "memory");')
    compaction.write_text(text)
    commands=tree/'target/protocol/command_table_target.c'
    text=commands.read_text()
    # Add a command in source without changing a count, address or linker size.
    import re
    declaration=re.search(r'const syscon_target_command_record syscon_target_commands\[\]\s*=\s*\{',text)
    assert declaration
    marker=declaration[0]
    text=text.replace(marker,marker+'\n    {"BUILD_INFO", syscon_target_cmd_version, 0, 0, "Build information from editable source"},')
    commands.write_text(text)
    linker=tree/'target/physical/firmware.ld'
    script=linker.read_text()
    assert script.count('.config_data :')==1
    script=script.replace('.config_data : {','.config_data : { . += 256;')
    assert script.count('.text_early : {')==1 and script.count('.text : {')==1
    script=script.replace('.text_early : {','.text_early : { . += 16;')
    script=script.replace('.text : {','.text : { . += 32;')
    assert script.count('.data : ALIGN(4) {')==1
    script=script.replace('__data_start = .;','__data_start = .; . += 64;')
    assert script.count('.peripheral_data : ALIGN(4) {')==1
    script=script.replace('__peripheral_data_start = .;',
                          '__peripheral_data_start = .; . += 8;')
    assert script.count('.irq_bss (NOLOAD) : {')==1
    script=script.replace('.irq_bss (NOLOAD) : {',
                          '.irq_bss (NOLOAD) : { . += 8;')
    script=script.replace('.application_rodata : {',
                          '.application_rodata : { . += 64;')
    script=script.replace('.command_table : {', '.command_table : { . += 28;')
    script=script.replace('__protocol_data_start = .;',
                          '__protocol_data_start = .; . += 4;')
    script=script.replace('.application_bss (NOLOAD) : {',
                          '.application_bss (NOLOAD) : { . += 8;')
    script=script.replace('.power_bss (NOLOAD) : {',
                          '.power_bss (NOLOAD) : { . += 8;')
    needle='__ram_exec_start = .; KEEP(*(.ram_original_flash))'
    assert script.count(needle)==1
    script=script.replace(needle,'__ram_exec_start = .; '+4*'SHORT(0xde00); '+'KEEP(*(.ram_original_flash))')
    # Exercise linker allocation within reclaimed SRAM with a different object
    # order. No production code knows either object's resulting address.
    order='*(.bss.syscon_timer_state) *(.bss.syscon_task_state)'
    assert script.count(order)==1
    script=script.replace(order,'*(.bss.syscon_task_state) *(.bss.syscon_timer_state)')
    order='*(.data.syscon_runtime_context) *(.data.syscon_runtime_current)'
    assert script.count(order)==1
    script=script.replace(order,'*(.data.syscon_runtime_current) *(.data.syscon_runtime_context)')
    order='*(.bss.syscon_modem_runtime) *(.bss.syscon_modem_boot) *(.bss.syscon_modem_timing)'
    assert script.count(order)==1
    script=script.replace(order,'*(.bss.syscon_modem_timing) *(.bss.syscon_modem_runtime) *(.bss.syscon_modem_boot)')
    linker.write_text(script)
    output=tmp_path/'physical'
    subprocess.run([sys.executable,str(tree/'tools/build_physical_firmware.py'),
                    '--output',str(output)],check=True,capture_output=True,text=True)
    manifest=json.loads((output/'manifest.json').read_text())
    assert manifest['status']=='linked-experimental'
    assert manifest['inputs_unchanged_during_build']
    assert not manifest['layout_audit']['issues']
    section=manifest['layout_audit']['sections']['.config_data']
    assert section['flags']==2 and section['bytes']>256
    assert section['address']+section['bytes']<=0xf7f8
    cache=manifest['layout_audit']['symbols']['syscon_config_state']
    data=manifest['layout_audit']['sections']['.data']
    assert data['address']<=cache<data['address']+data['bytes']
    assert cache>=data['address']+64
    return output,manifest,script


def test_source_added_compaction_workspace_keeps_stack_diagnostic_truthful(relocated_image,tmp_path):
    from build_physical_firmware import build
    from flash_interruptions import capture,compare_captures

    baseline=tmp_path/'baseline'
    layout=build(baseline)['layout_audit']
    current=capture((baseline/'firmware.bin').read_bytes(),'compact',
                    layout['stack_floor_address'],layout['symbols']['syscon_logger_target'])
    output,manifest,_=relocated_image
    edited=capture((output/'firmware.bin').read_bytes(),'compact',
                   manifest['layout_audit']['stack_floor_address'],
                   manifest['layout_audit']['symbols']['syscon_logger_target'])
    original=capture(load_image(),'compact',0x20000820,0x8f88)
    compare_captures(original,current)
    compare_captures(original,edited)
    # Each capture independently checked the diagnostic against live MSP.
    # The source edit must really enlarge the frame, not be optimized away.
    assert len(current['stack'])==len(edited['stack'])==1
    assert edited['stack'][0]['reported']>=current['stack'][0]['reported']+96


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
                     ('syscon_i2c_bus',0x2000013c),('syscon_i2c_state',0x20000760),
                     ('syscon_power_names',0x20000060),('syscon_minimum_vph_mv',0x2000005c),
                     ('syscon_shutdown_reason',0x2000036f),
                     ('syscon_usb_reattach_state',0x20000370),
                     ('syscon_shutdown_state',0x20000380),
                     ('syscon_key_events',0x200002d8),('syscon_key_event_buffer',0x200002d1),
                     ('syscon_console_parser',0x20000048),('syscon_console_buffer',0x200002ef),
                     ('syscon_ioexpander_initialized',0x200002d0),
                     ('syscon_shutdown_pending',0x200002ec),('syscon_key_started_off',0x200002ed),
                     ('syscon_wakeup_pending',0x20000680)]:
        assert symbols[name]!=old
    # A writer/reader pair retaining the same old callback address could still
    # agree with itself. Require registration in the actual relocated object.
    registered=int.from_bytes(machines[1].read(symbols['syscon_gpio_handlers'],4),'little')
    assert registered==symbols['syscon_target_powerkey_edge']
    # The former task/timer region now holds the linker-allocated state arena;
    # it is live memory, so only genuinely vacant locations are poisoned.
    obsolete=[(0x20000030,22),(0x2000005c,88),(0x2000036f,33),(0x200000da,3),
              (0x200000b4,36),(0x200000d8,2),(0x20000390,24),
              (0x20000685,11),(0x20000694,1)]
    # The old ADC table now holds relocated LED/PWM objects. Poison only the
    # unallocated prefix; a stale ADC lookup would instead encounter LED data.
    peripheral_start=manifest['layout_audit']['sections']['.peripheral_data']['address']
    if peripheral_start>0x200000f4:obsolete.append((0x200000f4,peripheral_start-0x200000f4))
    obsolete+= [(0x20000810,16),(0x200002d0,31),(0x20000680,1),(0x2000013c,12),(0x2000016c,200),(0x20000254,1),
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


@pytest.mark.parametrize('stack_bytes',[1280,1344])
def test_stack_guard_rejects_data_growth_that_exceeds_compaction_headroom(relocated_image,tmp_path,stack_bytes):
    output,manifest,script=relocated_image
    # Model a source edit adding ordinary state. The static minimum still
    # passes, but this leaves too little room for the exercised compaction path.
    extra=manifest['layout_audit']['stack_headroom_bytes']-stack_bytes
    assert extra>0
    script=script.replace('__extra_bss_start = .;',f'__extra_bss_start = .; . += {extra};')
    linker=tmp_path/'expanded-state.ld';linker.write_text(script)
    elf=tmp_path/'expanded-state.elf'
    objects=[str(p) for p in output.glob('*.o') if p.name!='physical-inputs.o']
    subprocess.run(['arm-none-eabi-gcc','-mcpu=cortex-m0plus','-mthumb','-nostdlib',
                    *objects,'-Wl,--gc-sections','-Wl,-T,'+str(linker),
                    '-o',str(elf)],check=True,capture_output=True,text=True)
    audit=elf_audit(elf)
    assert not audit['issues']
    assert audit['stack_headroom_bytes']==stack_bytes
    binary=tmp_path/'expanded-state.bin';emit_binary(elf,binary)
    engines=[]
    with pytest.raises(AssertionError,match='Stack overlaps allocated state'):
        legacy_compaction(binary.read_bytes(),b'%s/%u/%n',engines,stack_floor=audit['stack_floor_address'])
    assert engines
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
    obsolete=vacant_ranges(manifest,[(0x2000080c,1)])
    for address,size in obsolete:machines[1].write_ram(address,b'\xa5'*size)
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
    for address,size in obsolete:assert machines[1].read(address,size)==b'\xa5'*size


def test_relocated_power_routes_battery_detection_and_shutdown_commands(relocated_image):
    import re
    output,manifest,_=relocated_image
    symbols=manifest['layout_audit']['symbols']
    machines=[boot(load_image())[0],boot((output/'firmware.bin').read_bytes(),
              stack_floor=manifest['layout_audit']['stack_floor_address'])[0]]
    obsolete=vacant_ranges(manifest,[(0x2000005c,88),(0x2000036f,33)])
    for address,size in obsolete:machines[1].write_ram(address,b'\xa5'*size)
    battery_states=[]
    # External ADC stimuli cross the real battery-presence and NTC window
    # boundaries. Commands traverse UART, parser, ADC and expander code.
    for battery,ntc in [(3000,0),(2275,910),(2275,911),(1517,2732),(1517,2733),(2276,0)]:
        for machine in machines:
            machine.device.adc_inputs[2]=battery
            machine.device.adc_inputs[8]=ntc
        for command in ['BATCHECK','PWRSTATUS']:
            replies=[command_reply(machine,command) for machine in machines]
            assert all(b'PASS\r\n' in reply for reply in replies)
            assert normalized_log(replies[0])==normalized_log(replies[1])
        match=re.search(rb'Battery\s+: ([A-Z_]+) ',replies[1])
        assert match,replies[1]
        battery_states.append(match[1])
    assert len(set(battery_states))==2
    assert battery_states[0]==battery_states[2]==battery_states[3]==battery_states[5]
    assert battery_states[1]==battery_states[4]!=battery_states[0]
    for reason,name in enumerate(['REBOOT','POWEROFF','BATTERY_LOW','THERMAL_HIGH','THERMAL_LOW'],1):
        replies=[command_reply(machine,'SHUTDOWN_REASON '+name) for machine in machines]
        assert all(b'PASS\r\n' in reply for reply in replies)
        assert normalized_log(replies[0])==normalized_log(replies[1])
        assert machines[0].read(0x2000036f,1)==machines[1].read(symbols['syscon_shutdown_reason'],1)==bytes([reason])
    for address,size in obsolete:assert machines[1].read(address,size)==b'\xa5'*size


def test_relocated_diagnostic_controls_and_loop_counter(relocated_image):
    output,manifest,_=relocated_image
    symbols=manifest['layout_audit']['symbols']
    flag=symbols['syscon_diagnostics_enabled']
    state=symbols['syscon_diagnostics_state']
    assert flag!=0x20000046 and state!=0x200002c0
    machines=[boot(load_image())[0],boot((output/'firmware.bin').read_bytes(),
              stack_floor=manifest['layout_audit']['stack_floor_address'])[0]]
    obsolete=vacant_ranges(manifest,[(0x20000046,1),(0x200002c0,16)])
    for address,size in obsolete:machines[1].write_ram(address,b'\xa5'*size)
    before=machines[1].read(state,16)
    for enabled in [0,1,0,1]:
        replies=[command_reply(machine,'DIAG '+str(enabled)) for machine in machines]
        assert all(b'PASS\r\n' in reply for reply in replies)
        assert normalized_log(replies[0])==normalized_log(replies[1])
        assert machines[0].read(0x20000046,1)==machines[1].read(flag,1)==bytes([enabled])
    # Main-loop polling must update the linked object, not merely agree on a
    # stale fixed location. Timing/count values need not be instruction-identical.
    assert machines[1].read(state,16)!=before
    for address,size in obsolete:assert machines[1].read(address,size)==b'\xa5'*size


def test_source_added_command_and_help_use_linker_resolved_descriptors(relocated_image):
    output,manifest,_=relocated_image
    original,_=boot(load_image())
    candidate,_=boot((output/'firmware.bin').read_bytes(),stack_floor=candidate_stack_floor(output/'firmware.bin'))
    symbols=manifest['layout_audit']['symbols']
    count=int.from_bytes(candidate.read(symbols['syscon_target_command_count'],4),'little')
    original_count=len(__import__('inventory').command_table(load_image()))
    assert count==original_count+1
    assert symbols['syscon_target_commands']!=0xc419
    # Echo differs by design; both commands execute the same VERSION handler.
    expected=command_reply(original,'VERSION')
    actual=command_reply(candidate,'BUILD_INFO')
    assert b'Version=1.0.52\r\n' in expected and b'Version=1.0.52\r\n' in actual
    assert b'PASS\r\n' in actual
    help_text=command_reply(candidate,'HELP')
    assert b'BUILD_INFO - Build information from editable source' in help_text
    for command in __import__('inventory').command_table(load_image()):
        assert (command['name']+' - '+command['help']).encode() in help_text
    flag=symbols['syscon_protocol_debug']
    assert flag!=0x200002ee
    for command,value in [('560D_DBG ON',1),('560D_DBG OFF',0)]:
        replies=[command_reply(m,command) for m in (original,candidate)]
        assert normalized_log(replies[0])==normalized_log(replies[1])
        assert candidate.read(flag,1)==bytes([value])
