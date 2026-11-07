"""Configuration text is editable source, not an original-flash address contract."""
import gc

import pytest

import build_runtime_scan_image as runtime
from config_helpers_oracle import build, logger_arguments
from test_config_helpers import controller_pair, compare_controllers, slot, KEY, VALUE, OUT, SLOT
from test_config_target_updates import bind_diagnostic_ports


@pytest.fixture(scope='module')
def config_image(tmp_path_factory):
    return build(tmp_path_factory.mktemp('relocatable-config'))


@pytest.fixture(scope='module', autouse=True)
def retain_engines():
    from config_helpers_oracle import ConfigHelperPair
    gc.collect()
    ConfigHelperPair.owners=[]
    yield
    ConfigHelperPair.owners=None
    gc.collect()


def test_configuration_works_when_original_private_text_and_defaults_are_poisoned(config_image):
    p=controller_pair(config_image)
    # Only the rebuilt image loses this original-data dependency. The reference
    # remains an independent oracle with its original read-only contents.
    p.candidate.put(0xacfa,b'\xa5'*(0xb24c-0xacfa))
    bind_diagnostic_ports(p)
    p.call(0x30f0,'syscon_target_config_init',returns=False,same_stack=True)
    compare_controllers(p)
    for i in range(20):
        key=[b'sys.auto_boot',b'sys.edl_timer',b'user.mode'][i%3]
        value=[b'true' if i%2 else b'false',str(i).encode(),b'value'+str(i).encode()][i%3]
        p.put(KEY,key+b'\0');p.put(VALUE,value+b'\0')
        p.call(0x32c8,'syscon_cfg_runtime_update',KEY,VALUE,same_stack=True)
        compare_controllers(p)
        p.put(OUT,b'\xa5'*32)
        p.call(0x339c,'syscon_cfg_runtime_get',KEY,OUT,same_stack=True)
        p.equal(OUT,32)
    assert any(event[0]=='uart' for event in p.events[0])


def test_editing_message_length_changes_real_uart_output_without_address_edits(tmp_path,monkeypatch):
    header=(runtime.ROOT/'include/config_text.h').read_text()
    original='Key checksum mismatch'
    replacement='Configuration key checksum mismatch (edited source text)'
    assert header.count('"'+original+'"')==1
    shadow=tmp_path/'include';shadow.mkdir()
    (shadow/'config_text.h').write_text(header.replace('"'+original+'"','"'+replacement+'"'))
    # A compiler include override builds a deliberate source variant without
    # modifying the production tree or patching a running image.
    monkeypatch.setattr(runtime,'FLAGS',[*runtime.FLAGS,'-I'+str(shadow)])
    image=build(tmp_path/'variant')
    p=controller_pair(image);bind_diagnostic_ports(p)
    malformed=slot(b'key',b'value');malformed[31]^=1;p.put(SLOT,malformed)
    assert p.original.call(0x2840,SLOT)==0
    assert p.candidate.call('syscon_cfg_slot_valid',SLOT)==0
    outputs=[b''.join(event[1] for event in events if event[0]=='uart') for events in p.events]
    assert original.encode() in outputs[0]
    assert replacement.encode() in outputs[1]
    assert outputs[0].replace(original.encode(),replacement.encode())==outputs[1]
    assert (runtime.ROOT/'include/config_text.h').read_text()==header


class LoggerCPU:
    def __init__(self,base,number=7,text=b'value',fmt=b'%s %d %%'):
        self.cpu=self
        self.memory={}
        self.arguments=[1,base,base+32,base+96,number]
        for address,value in [(base,b'CONF'),(base+32,fmt),(base+96,text)]:
            self.memory.update({address+i:byte for i,byte in enumerate(value+b'\0')})
    def arg(self,index):return self.arguments[index]
    def mem_read(self,address,length):return bytes(self.memory[address+i] for i in range(length))


def test_logger_comparison_accepts_relocation_but_rejects_changed_payloads():
    left=logger_arguments(LoggerCPU(0x1000,number=0x20000400))
    assert left==logger_arguments(LoggerCPU(0x3000,number=0x20000400))
    assert left!=logger_arguments(LoggerCPU(0x3000,number=0x20000401))
    assert left!=logger_arguments(LoggerCPU(0x3000,number=0x20000400,text=b'changed'))
    assert left!=logger_arguments(LoggerCPU(0x3000,number=0x20000400,fmt=b'%s/%d %%'))
    with pytest.raises(AssertionError):logger_arguments(LoggerCPU(0x1000,fmt=b'%q'))


def test_changed_text_and_relocated_linked_data_keep_reset_uart_and_persistence(tmp_path):
    import json
    import shutil
    import subprocess
    import sys
    from rebuilt_system import compare,boot,command_reply,normalized_log
    from inventory import load_image

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
    result=compare((output/'firmware.bin').read_bytes())
    assert result['persistent_flash_equal']
    assert all(session['equal_after_timestamp_normalization'] for session in result['sessions'])
    assert not result['firmware_function_replacements']
    assert result['rebuilt']['minimum_msp_during_session']>=manifest['layout_audit']['symbols']['__extra_bss_end']

    # Exercise the actual cache consumers through UART after moving SRAM and
    # poisoning the old cache. No handler replacement or guest code patching.
    machines=[boot(image)[0] for image in [load_image(),(output/'firmware.bin').read_bytes()]]
    poison=b'\xa5'*22
    machines[1].cpu.mem_write(0x20000030,poison)
    obsolete=[(0x200000da,3),(0x20000534,216),(0x20000610,112)]
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

    # Legacy values must also remain literal after recompilation moves code,
    # constants and SRAM. No reserved byte at a private return address is needed.
    from test_rebuilt_system import legacy_compaction
    literal=b"%s/%u/%n"
    persisted,value,_=legacy_compaction((output/'firmware.bin').read_bytes(),literal,machines)
    assert value==literal
    assert persisted[64:128]==bytes(slot(b'legacy',literal))
