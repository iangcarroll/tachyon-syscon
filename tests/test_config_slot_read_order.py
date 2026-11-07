"""Original slot validation snapshots, live error rereads and byte fault order."""
import gc
import pytest
from unicorn import UC_HOOK_MEM_READ,UC_HOOK_CODE
from unicorn.arm_const import UC_ARM_REG_PC
from config_helpers_oracle import build,ConfigHelperPair,logger_arguments

class ReadBoundary(Exception):
    """Explicit environment failure at an attempted byte read, not MCU reset."""

@pytest.fixture(scope='module')
def image(tmp_path_factory):return build(tmp_path_factory.mktemp('slot-read-order'))
@pytest.fixture(scope='module',autouse=True)
def retained_engines():
    gc.collect();engines=[]
    yield engines
    engines.clear();gc.collect()

def encoded(key=b'a',value=b'b'):
    slot=bytearray(b'\xff'*64)
    for offset,text in [(0,key),(32,value)]:
        slot[offset:offset+len(text)+1]=text+b'\0';checksum=0
        for byte in slot[offset:offset+31]:checksum^=byte
        slot[offset+31]=checksum
    return slot


def run_pair(image,owners,slot,base=0x20000400,mutation=None,fault_read=None):
    pair=ConfigHelperPair(image);owners.append(pair);pair.put(base,slot);rows=[]
    for cpu,entry,checksum,logger in [
        (pair.original,0x2840,0x282c,0x8f88),
        (pair.candidate,pair.candidate.symbols['syscon_cfg_slot_valid'],
         pair.candidate.symbols['syscon_cfg_checksum']&~1,pair.candidate.symbols['syscon_target_logger']&~1)]:
        reads=[];logs=[];changed=False
        def read(uc,access,address,size,value,user):
            nonlocal changed
            reads.append((address-base,size))
            if fault_read==len(reads):raise ReadBoundary(address-base,size)
            if mutation is not None and not changed and address==base and uc.reg_read(UC_ARM_REG_PC)==checksum+8:
                offset,replacement=mutation;uc.mem_write(base+offset,bytes([replacement]));changed=True
        def log(uc,address,size,user):
            # Observe the real disabled logger's defined arguments only.
            logs.append(logger_arguments(cpu))
        cpu.cpu.hook_add(UC_HOOK_MEM_READ,read,begin=base,end=base+63)
        cpu.cpu.hook_add(UC_HOOK_CODE,log,begin=logger,end=logger)
        try:result=('return',cpu.call(entry,base))
        except ReadBoundary as error:result=('read-fault',*error.args)
        rows.append(dict(result=result,reads=reads,logs=logs,changed=changed,
                         memory=bytes(cpu.cpu.mem_read(base,64))))
    assert rows[0]==rows[1],rows
    return rows[0]


@pytest.mark.parametrize('base',[0x20000400,0xfc00])
@pytest.mark.parametrize('case',['valid','bad-key-checksum','bad-value-checksum','invalid-key','semicolon-key'])
def test_stable_sram_and_main_slots_keep_ordered_byte_reads(image,retained_engines,base,case):
    slot=encoded()
    if case=='bad-key-checksum':slot[31]^=1
    elif case=='bad-value-checksum':slot[63]^=1
    elif case=='invalid-key':slot[0]=ord('%')
    elif case=='semicolon-key':slot=encoded(b'a;%s')
    run_pair(image,retained_engines,slot,base=base)


@pytest.mark.parametrize('offset',[31,63])
def test_stored_checksum_mutation_after_snapshot_preserves_original_acceptance(image,retained_engines,offset):
    slot=encoded()
    result=run_pair(image,retained_engines,slot,mutation=(offset,slot[offset]^1))
    assert result['changed'] and result['result']==('return',1)


def test_failed_value_check_diagnostic_rereads_changed_stored_byte(image,retained_engines):
    slot=encoded();slot[63]^=1
    result=run_pair(image,retained_engines,slot,mutation=(63,slot[63]^2))
    assert result['result']==('return',0) and result['changed']
    assert result['logs'][-1][-1]==slot[63]^2


@pytest.mark.parametrize('fault_read',range(1,69))
def test_first_failing_read_matches_at_every_valid_slot_read_boundary(image,retained_engines,fault_read):
    result=run_pair(image,retained_engines,encoded(),fault_read=fault_read)
    assert result['result'][0]=='read-fault'
    assert len(result['reads'])==fault_read


def test_live_error_byte_reread_fault_boundary(image,retained_engines):
    slot=encoded();slot[63]^=1
    successful=run_pair(image,retained_engines,slot)
    result=run_pair(image,retained_engines,slot,fault_read=len(successful['reads']))
    assert result['result']==('read-fault',63,1)
