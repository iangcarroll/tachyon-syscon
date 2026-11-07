"""Freshly compiled source image, exact MCU map, real reset/IRQ/persistence."""
import json
import re
import pytest
from build_physical_firmware import build, ROOT
from rebuilt_system import boot, command_reply, compare, normalized_log, SCENARIO
from emulate import from_scenario
from unicorn.arm_const import UC_ARM_REG_PRIMASK


@pytest.fixture(scope='module')
def rebuilt_image(tmp_path_factory):
    directory=tmp_path_factory.mktemp('rebuilt-system')
    manifest=build(directory)
    assert manifest['status']=='linked-experimental'
    assert manifest['inputs_unchanged_during_build']
    assert manifest['unresolved_symbols']==[]
    assert manifest['layout_audit']['issues']==[]
    assert not manifest['endpoint_stubs_included']
    assert not manifest['original_executable_bytes_included']
    return (directory/'firmware.bin').read_bytes()


def test_complete_source_reset_uart_and_configuration_fresh_boot(rebuilt_image):
    result=compare(rebuilt_image)
    assert result['persistent_flash_equal']
    assert result['firmware_function_replacements']==[]
    for role in ['original','rebuilt']:
        state=result[role]
        assert state['boot_observation']['main_loop_reached']
        assert state['minimum_msp_during_session']>=0x20000820
        assert '0x20000000' in state['executed_addresses']
        exceptions=[event[:2] for event in state['exception_events']]
        # This firmware uses polling for the I2C transactions in this session;
        # the actual asynchronous sources exercised here are SysTick and UART0.
        for vector in [15,31]:
            assert ['exception-enter',vector] in exceptions or ('exception-enter',vector) in exceptions
            assert ['exception-return',vector] in exceptions or ('exception-return',vector) in exceptions


def test_source_image_i2c_nack_negative_control_reaches_real_assertion(rebuilt_image,tmp_path):
    inputs=json.loads(SCENARIO.read_text());inputs['i2c_failures']=['nack']*4
    scenario=tmp_path/'nack.json';scenario.write_text(json.dumps(inputs))
    machines=[from_scenario(scenario,image)[0] for image in [None,rebuilt_image]]
    outputs=[]
    for machine in machines:
        machine.run(1000000)
        output=bytes(machine.device.tx[0])
        assert b'Assertion failed:' in output
        assert machine.cpu.reg_read(UC_ARM_REG_PRIMASK)==1
        assert not machine.systick_ctrl&2
        assert machine.device.expander.events
        outputs.append(normalized_log(output))
    assert outputs[0]==outputs[1]


@pytest.fixture(scope='module')
def legacy_engines():
    engines=[]
    yield engines
    engines.clear()


def legacy_compaction(image,value,engines,stack_floor=0x20000820):
    from test_config_helpers import slot
    image=bytearray(image.ljust(65536,b'\xff'))
    image[0xfc00:]=slot(b'confVersion',b'1')+slot(b'legacy',value)*14+b'\xff'*64
    machine,_=boot(bytes(image),stack_floor=stack_floor);engines.append(machine)
    before=bytes(machine.flash[0xfc00:])
    output=command_reply(machine,'CONFIG_SET new value')
    assert b'Compaction complete:' in output and b'[MFGD] PASS\r\n' in output
    after=bytes(machine.flash[0xfc00:]);assert after!=before
    reply=command_reply(machine,'CONFIG_GET legacy')
    match=re.search(rb'\[MFGD\] legacy = ([^\r]*)\r\n',reply)
    assert match and b'[MFGD] PASS\r\n' in reply
    return after,match.group(1),normalized_log(output+reply)


@pytest.mark.parametrize('value',[b'%s',b'%u'])
def test_legacy_compaction_preserves_literal_uart_output_and_persistence(rebuilt_image,legacy_engines,value):
    original=legacy_compaction((ROOT/'firmware/syscon-1.0.52.bin').read_bytes(),value,legacy_engines)
    rebuilt=legacy_compaction(rebuilt_image,value,legacy_engines)
    assert rebuilt[1]==value and original[1]!=value
    from test_config_helpers import slot
    assert rebuilt[0][64:128]==bytes(slot(b'legacy',value))
    # A fresh CPU must read the literal value from the persisted sector as well.
    persisted=bytearray(rebuilt_image.ljust(65536,b'\xff'));persisted[0xfc00:]=rebuilt[0]
    machine,_=boot(bytes(persisted));legacy_engines.append(machine)
    reply=command_reply(machine,'CONFIG_GET legacy')
    assert b'legacy = '+value+b'\r\n' in reply and b'PASS\r\n' in reply


def test_public_configuration_still_rejects_format_metacharacters(rebuilt_image,legacy_engines):
    machines=[boot(image)[0] for image in [(ROOT/'firmware/syscon-1.0.52.bin').read_bytes(),rebuilt_image]]
    legacy_engines.extend(machines)
    before=[bytes(machine.flash[0xf800:]) for machine in machines]
    for value in ['%s','%u','%n']:
        replies=[command_reply(machine,'CONFIG_SET rejected '+value) for machine in machines]
        assert all(b'FAIL\r\n' in reply for reply in replies)
        assert normalized_log(replies[0])==normalized_log(replies[1])
    assert [bytes(machine.flash[0xf800:]) for machine in machines]==before


def test_raw_rgb_format_commands_preserve_real_logger_register_effects(rebuilt_image,legacy_engines):
    machines=[boot(image)[0] for image in [(ROOT/'firmware/syscon-1.0.52.bin').read_bytes(),rebuilt_image]]
    legacy_engines.extend(machines)
    # The original command prints each short token as a format without passing
    # arguments. Its missing R1 argument is the real previous printer's result.
    # A mocked printer previously hid the UART/logger register-clobber mismatch.
    for token in ['0','%u','%s','%p','%d','%x','%c','%3u']:
        command=f'SET_RGB {token}:2:3:4:0:'
        outputs=[command_reply(machine,command) for machine in machines]
        assert all(b'[MFGD] PASS\r\n' in output for output in outputs)
        assert normalized_log(outputs[0])==normalized_log(outputs[1]),command
