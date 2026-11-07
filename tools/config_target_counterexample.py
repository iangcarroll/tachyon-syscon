"""Replay the approved literal-preservation correction against the original bug.

This intentional difference is not an equivalence proof.
"""
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from config_helpers_oracle import build
from test_config_helpers import controller_pair,slot,KEY,VALUE

def record(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    pair=controller_pair(build(destination))
    data=bytes(slot(b'legacy',b'%u'))*15+b'\xff'*64
    pair.put(0xfc00,data);pair.put(KEY,b'new\0');pair.put(VALUE,b'value\0')
    assert pair.original.call(0x32c8,KEY,VALUE,count=1000000)==1
    assert pair.candidate.call('syscon_cfg_runtime_update',KEY,VALUE,count=1000000)==1
    flash=[bytes(cpu.cpu.mem_read(0xfc00,1024)) for cpu in (pair.original,pair.candidate)]
    expected=bytes(slot(b'new',b'value'))+bytes(slot(b'legacy',b'%u'))+b'\xff'*896
    assert flash[1]==expected and flash[0]!=expected
    result=dict(kind='approved-literal-preservation-correction',original_entry='0x32c8',rebuilt_entry='syscon_cfg_runtime_update',
        initial_runtime_sector_hex=data.hex(),new_key='new',new_value='value',
        retained_legacy_value='%u',original_restored_value=flash[0][96:126].split(b'\0')[0].decode('ascii'),
        rebuilt_restored_value=flash[1][96:126].split(b'\0')[0].decode('ascii'),
        cause='Original formatting consumed an omitted variadic argument. The C implementation now preserves stored text literally, removing the private return-address dependency.',
        historical_witness='analysis/config-target-vararg-counterexample.json',
        full_equivalence=False,hardware_access=False)
    path=destination/'literal-preservation.json'
    path.write_text(json.dumps(result,indent=2)+'\n');print(path)
    print(json.dumps({k:result[k] for k in ['original_restored_value','rebuilt_restored_value','full_equivalence']}))
    return result
if __name__=='__main__':record(ROOT/'build/config-vararg-counterexample')
