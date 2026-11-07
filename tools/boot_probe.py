"""Locate the first unsupported boot interaction; this does not fake a boot pass."""
import json
from unicorn import UC_HOOK_MEM_INVALID, UcError
from unicorn.arm_const import UC_ARM_REG_PC
from inventory import ROOT
from oracle import Oracle

o=Oracle()
failures=[]
def unknown(cpu,access,address,size,value,_):
    failures.append(dict(pc=cpu.reg_read(UC_ARM_REG_PC), access=access,
                         address=address,size=size,value=value))
    return False
o.cpu.hook_add(UC_HOOK_MEM_INVALID,unknown)
try:
    o.call(0x79f0)
except (UcError,RuntimeError) as e:
    result=dict(full_boot_passed=False,reason=str(e),unsupported=failures,
                executed_instruction_addresses=sorted(o.executed),hooks=[])
    (ROOT/'analysis/boot-probe.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='executed_instruction_addresses'},indent=2))
else:
    raise SystemExit('Unexpected reset return: investigate before accepting any boot result')
