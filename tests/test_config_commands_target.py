"""Real command parsing through source configuration helpers and FLASHCTL."""
import random
import re
import struct
import pytest
from config_helpers_oracle import ConfigHelperPair
from config_commands_target_oracle import build,MAPPINGS,GETTERS
from test_config_helpers import controller_pair,compare_controllers,slot
from test_protocol_target import string
from unicorn import UC_HOOK_MEM_WRITE
ARGS=0x20000840

@pytest.fixture(scope='module')
def commands_elf(tmp_path_factory):return build(tmp_path_factory.mktemp('config-commands-target'))

class Pair:
    def __init__(self,elf):
        self.p=controller_pair(elf);self.outputs=[[],[]];self.watchdogs=[0,0];self.reads=[[],[]]
        self.values={a:0 for a in GETTERS};self.mutate_output=None
        self.printers=[0x10041,self.p.candidate.callback(lambda cpu:self.output(cpu,1))]
        self.p.original.hooks[0x10040]=lambda cpu:self.output(cpu,0)
        for i,cpu in enumerate((self.p.original,self.p.candidate)):
            for address,name in GETTERS.items():
                entry=address if i==0 else cpu.symbols['syscon_target_'+name]&~1
                def get(machine,i=i,address=address):self.reads[i].append(address);return self.values[address]
                cpu.hooks[entry]=get
            def feed(uc,kind,address,size,value,_,i=i):self.watchdogs[i]+=1
            cpu.cpu.hook_add(UC_HOOK_MEM_WRITE,feed,begin=0x40081108,end=0x40081108)
    def output(self,cpu,i):
        fmt=string(cpu,cpu.arg(0));formats=re.findall(rb'%(?!%)[-+ #0]*[0-9.*]*[hl]*([diuxXscp])',fmt)
        args=[]
        for index,spec in enumerate(formats):
            v=cpu.arg(index+1);args.append(string(cpu,v) if spec==b's' else v)
        self.outputs[i].append((fmt,tuple(args)))
        if self.mutate_output:self.mutate_output(cpu,i)
        return 0
    def call(self,address,args=b''):
        self.outputs=[[],[]];self.watchdogs=[0,0];self.reads=[[],[]]
        self.p.put(ARGS,args+b'\0');results=[]
        for i,cpu in enumerate((self.p.original,self.p.candidate)):
            results.append(cpu.call(address if i==0 else 'syscon_target_'+MAPPINGS[address],ARGS,self.printers[i],count=3000000))
        assert results[0]==results[1]
        assert self.outputs[0]==self.outputs[1],self.outputs
        assert self.watchdogs[0]==self.watchdogs[1]
        assert self.reads[0]==self.reads[1]
        compare_controllers(self.p)
        return results[0]


def test_config_commands_real_scan_key_value_limits_and_invalid_inputs(commands_elf):
    p=Pair(commands_elf)
    for value in [b'',b':',b'key',b'key:',b':value:',b'key:value',b'key:value:',
                  b'k'*31+b':v:',b'k'*32+b':v:',b'key:'+b'v'*31+b':',b'key:bad%:',
                  b'key:bad;tail:',b'key:v:extra',b' key :value:']:
        for address in [0x4490,0x44dc,0x4638,0x4714,0x4684,0x4760]:p.call(address,value)


def test_config_commands_append_find_get_update_and_dump_through_flash(commands_elf):
    p=Pair(commands_elf)
    for namespace,set_entry,get_entry,find_entry,dump in [('identity',0x4684,0x4638,0x4490,0x45e0),('runtime',0x4760,0x4714,0x44dc,0x45ec)]:
        for i in range(20):
            p.call(set_entry,f'key{i%5}:value{i}:'.encode());p.call(get_entry,f'key{i%5}:'.encode())
        for key in [b'0:',b'1:',b'-1:',b'99999999999999999999:',b'notnumber:']:p.call(find_entry,key)
        p.call(dump)
    # Only read-only disabled logger, watchdog and the final printer are leaves;
    # scan, namespace/store, validation and flash command bodies execute.
    assert p.p.controllers[0].events==p.p.controllers[1].events


def test_config_dump_rejected_and_blank_slots_and_watchdog_each_iteration(commands_elf):
    p=Pair(commands_elf)
    for base,entry,count in [(0xf800,0x45e0,16),(0xfc00,0x45ec,15)]:
        flash=bytearray(b'\xff'*1024);flash[:64]=slot(b'good',b'value');flash[64:128]=slot(b'bad',b'value');flash[95]^=1
        p.p.put(base,flash);p.call(entry)
        assert p.watchdogs[0]==p.watchdogs[1] and p.watchdogs[0]>=count
        assert any(b'REJECTED' in fmt for fmt,args in p.outputs[0])
        assert any(b'WARNING' in fmt for fmt,args in p.outputs[0])


def test_config_erase_password_and_scan_validation(commands_elf):
    p=Pair(commands_elf)
    for entry,password in [(0x45f8,b'B23000'),(0x46d4,b'particle')]:
        for value in [b'',b':',b'wrong:',password.lower()+b':',password+b':',password+b'!:']:
            p.call(entry,value)


def test_config_internal_snapshots_getters_before_output_callbacks(commands_elf):
    p=Pair(commands_elf);rng=random.Random(0x3fdc)
    for _ in range(50):
        p.values={a:rng.choice([0,1,255,0xffffffff]) for a in GETTERS}
        p.call(0x3fdc)
        assert p.reads[0]==list(GETTERS)


def test_config_compaction_preserves_legacy_missing_argument_value_and_live_slot_aliases(commands_elf):
    p=Pair(commands_elf)
    for legacy in [b'%u',b'%x',b'%08X',b'%d/%u/%x',b'[%u]%u%u%u',b'%%-%u']:
        p.p.put(0xfc00,bytes(slot(b'legacy',legacy))*15+b'\xff'*64)
        p.call(0x4760,b'new:value:')
        p.call(0x4714,b'legacy:')


def test_direct_write_slot_uses_original_missing_first_argument_at_same_stack_address(commands_elf):
    # Pointer-valued formatting requires the same physical stack placement;
    # comparing relocated pointer text would hide a real ABI dependency.
    from test_config_helpers import KEY,VALUE
    p=controller_pair(commands_elf)
    for key,value in [(b'%u',b'literal'),(b'%08x',b'%u/%u/%u'),(b'%%-%u',b'%%-%u')]:
        p.put(0xf800,b'\xff'*2048);p.put(KEY,key+b'\0');p.put(VALUE,value+b'\0')
        p.call(0x28d4,'syscon_cfg_write_slot',0xf800,KEY,VALUE,same_stack=True)
        compare_controllers(p)
