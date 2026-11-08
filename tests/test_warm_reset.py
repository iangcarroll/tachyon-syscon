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
        m,_=boot(image,stack_floor=0x20000820 if image==load_image() else symbols['__extra_bss_end'])
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
        adc_blocks=([(0x200000f4,72),(0x20000685,11),(0x20000694,1)]
                    if image==load_image() else
                    [(symbols['syscon_adc_channels'],72),
                     (symbols['syscon_adc_state'],11),
                     (symbols['syscon_adc_vref_initialized'],1)])
        for address,size in adc_blocks:m.write_ram(address,b'\xa5'*size)
        led_blocks=([(0x20000148,36),(0x200003a8,28)]
                    if image==load_image() else
                    [(symbols['syscon_pwm_channels'],36),
                     (symbols['syscon_rgb_runtime'],28)])
        for address,size in led_blocks:m.write_ram(address,b'\xa5'*size)
        gpio_i2c_blocks=([(0x2000016c,200),(0x20000698,200),(0x20000254,1),
                          (0x2000013c,12),(0x20000760,2)]
                         if image==load_image() else
                         [(symbols['syscon_gpio_pins'],200),
                          (symbols['syscon_gpio_handlers'],200),
                          (symbols['syscon_reset_cause_cache'],1),
                          (symbols['syscon_i2c_bus'],12),
                          (symbols['syscon_i2c_state'],2)])
        for address,size in gpio_i2c_blocks:m.write_ram(address,b'\xa5'*size)
        uart_blocks=([(0x20000234,32),(0x20000762,18),(0x20000774,152)]
                     if image==load_image() else
                     [(symbols['syscon_uart_ports'],32),
                      (symbols['syscon_uart_config'],18),
                      (symbols['syscon_uart_rings'],152)])
        for address,size in uart_blocks:m.write_ram(address,b'\xa5'*size)
        power_blocks=([(0x2000005c,4),(0x2000036f,1),(0x20000370,16),(0x20000380,16)]
                      if image==load_image() else
                      [(symbols['syscon_minimum_vph_mv'],4),(symbols['syscon_shutdown_reason'],1),
                       (symbols['syscon_usb_reattach_state'],16),(symbols['syscon_shutdown_state'],16)])
        names=0x20000060 if image==load_image() else symbols['syscon_power_names']
        for address,size in [*power_blocks,(names,84)]:m.write_ram(address,b'\xa5'*size)
        def power_names():
            result=[]
            for offset in range(0,84,4):
                address=int.from_bytes(m.read(names+offset,4),'little')
                result.append(bytes(m.read(address,64)).split(b'\0',1)[0])
            return tuple(result)
        diagnostic_blocks=([(0x20000046,1),(0x200002c0,16)]
                           if image==load_image() else
                           [(symbols['syscon_diagnostics_enabled'],1),
                            (symbols['syscon_diagnostics_state'],16)])
        for address,size in diagnostic_blocks:m.write_ram(address,b'\xa5'*size)
        app_blocks=([(0x200002d1,4),(0x200002ec,1),(0x200002ed,1),(0x20000680,1),
                     (0x200002d0,1),(0x200002ef,128)] if image==load_image() else
                    [(symbols['syscon_key_event_buffer'],4),(symbols['syscon_shutdown_pending'],1),
                     (symbols['syscon_key_started_off'],1),(symbols['syscon_wakeup_pending'],1),
                     (symbols['syscon_ioexpander_initialized'],1),(symbols['syscon_console_buffer'],128)])
        queue=0x200002d8 if image==load_image() else symbols['syscon_key_events']
        console=0x20000048 if image==load_image() else symbols['syscon_console_parser']
        for address,size in [*app_blocks,(queue,20),(console,20)]:m.write_ram(address,b'\xa5'*size)
        def application_state():
            # Validate pointer targets against their owning objects, then compare
            # values. No private pointer bytes are part of the behavior contract.
            queue_buffer=app_blocks[0][0]
            console_buffer=app_blocks[-1][0]
            assert int.from_bytes(m.read(queue,4),'little')==queue_buffer
            assert int.from_bytes(m.read(console+4,4),'little')==console_buffer
            printer=0x8fa1 if image==load_image() else symbols['syscon_target_mfg_logger']
            assert int.from_bytes(m.read(console+16,4),'little')==printer
            return (tuple(m.read(address,size) for address,size in app_blocks),
                    m.read(queue+4,16),m.read(console,4),m.read(console+8,8))
        modem_blocks=([(0x200003c4,12),(0x20000450,16),(0x200004e0,84),
                       (0x200003d0,128),(0x20000460,128)] if image==load_image() else
                      [(symbols['syscon_modem_boot'],12),(symbols['syscon_modem_timing'],16),
                       (symbols['syscon_modem_runtime'],84),(symbols['syscon_modem_scratch'],128),
                       (symbols['syscon_modem_buffer'],128)])
        modem_parser=0x200000e0 if image==load_image() else symbols['syscon_modem_parser']
        for address,size in [*modem_blocks,(modem_parser,20)]:m.write_ram(address,b'\xa5'*size)
        def modem_state():
            assert int.from_bytes(m.read(modem_parser+4,4),'little')==modem_blocks[-1][0]
            printer=0x5edd if image==load_image() else symbols['syscon_target_sg560d_printf']
            assert int.from_bytes(m.read(modem_parser+16,4),'little')==printer
            return (tuple(m.read(address,size) for address,size in modem_blocks),
                    m.read(modem_parser,4),m.read(modem_parser+8,8))
        current=0x20000258 if image==load_image() else symbols['syscon_runtime_current']
        context=0x2000025c if image==load_image() else symbols['syscon_runtime_context']
        heap=0x20000810 if image==load_image() else symbols['syscon_runtime_heap']
        for address,size in [(current,4),(context,100),(heap,16)]:m.write_ram(address,b'\xa5'*size)
        def runtime_state():
            assert int.from_bytes(m.read(current,4),'little')==context
            streams=[]
            for offset,old,name in [(4,0xe294,'input'),(8,0xe2b4,'output'),(12,0xe274,'error')]:
                pointer=int.from_bytes(m.read(context+offset,4),'little')
                assert pointer==(old if image==load_image() else symbols['syscon_stdio_'+name])
                streams.append(m.read(pointer,32))
            return m.read(context,4),tuple(streams),m.read(context+16,84),m.read(heap,16)
        protocol_debug=0x200002ee if image==load_image() else symbols['syscon_protocol_debug']
        m.write_ram(protocol_debug,b'\xa5')
        log_flag=0x2000080c if image==load_image() else symbols['syscon_log_enabled']
        m.write_ram(log_flag,b'\xa5')
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
                               tuple(m.read(address,size) for address,size in button_blocks),
                               tuple(m.read(address,size) for address,size in adc_blocks),
                               tuple(m.read(address,size) for address,size in led_blocks),
                               tuple(m.read(address,size) for address,size in gpio_i2c_blocks),
                               tuple(m.read(address,size) for address,size in uart_blocks),
                               m.read(log_flag,1),m.read(protocol_debug,1),application_state(),
                               tuple(m.read(address,size) for address,size in power_blocks),
                               power_names(),runtime_state(),modem_state(),
                               tuple(m.read(address,size) for address,size in diagnostic_blocks)))
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
