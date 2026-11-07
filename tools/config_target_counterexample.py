"""Replay the historical legacy-format mismatch as a scoped local regression.

Matching this witness is not a whole-domain equivalence proof.
"""
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
from config_helpers_oracle import build
from test_config_helpers import controller_pair,compare_controllers,slot,KEY,VALUE

def record(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    pair=controller_pair(build(destination))
    data=bytes(slot(b'legacy',b'%u'))*15+b'\xff'*64
    pair.put(0xfc00,data);pair.put(KEY,b'new\0');pair.put(VALUE,b'value\0')
    pair.call(0x32c8,'syscon_cfg_runtime_update',KEY,VALUE)
    compare_controllers(pair)
    flash=[bytes(cpu.cpu.mem_read(0xfc00,1024)) for cpu in (pair.original,pair.candidate)]
    assert flash[0]==flash[1]
    result=dict(kind='historical-inequivalence-regression-now-matching',original_entry='0x32c8',rebuilt_entry='syscon_cfg_runtime_update',
        initial_runtime_sector_hex=data.hex(),new_key='new',new_value='value',
        retained_legacy_value='%u',original_restored_value=flash[0][96:126].split(b'\0')[0].decode('ascii'),
        rebuilt_restored_value=flash[1][96:126].split(b'\0')[0].decode('ascii'),
        cause='Original omitted variadic R3 carried the saved original return address; the reconstructed ABI shim now preserves this logical value and the live slot argument frame.',
        historical_witness='analysis/config-target-vararg-counterexample.json',
        full_equivalence=False,hardware_access=False)
    path=ROOT/'analysis/config-target-vararg-regression.json'
    path.write_text(json.dumps(result,indent=2)+'\n');print(path)
    print(json.dumps({k:result[k] for k in ['original_restored_value','rebuilt_restored_value','full_equivalence']}))
    return result
if __name__=='__main__':record(ROOT/'build/config-vararg-counterexample')
