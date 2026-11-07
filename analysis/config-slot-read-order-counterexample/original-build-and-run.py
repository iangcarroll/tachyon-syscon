from pathlib import Path
import json,struct
from unicorn import UC_HOOK_MEM_READ
from unicorn.arm_const import UC_ARM_REG_PC
from config_helpers_oracle import build,ConfigHelperPair
BASE=0x20000400
slot=bytearray(b'\xff'*64)
for off,text in [(0,b'a'),(32,b'b')]:
 slot[off:off+len(text)+1]=text+b'\0';cs=0
 for v in slot[off:off+31]:cs^=v
 slot[off+31]=cs
elf=build('/tmp/syscon-slot-before');p=ConfigHelperPair(elf);p.put(BASE,slot);rows=[]
for role,cpu,entry,checksum in [('original',p.original,0x2840,0x282c),('rebuilt',p.candidate,p.candidate.symbols['syscon_cfg_slot_valid'],p.candidate.symbols['syscon_cfg_checksum']&~1)]:
 reads=[];changed=[False]
 def read(uc,access,address,size,value,user):
  reads.append([address-BASE,size])
  if not changed[0] and address==BASE and uc.reg_read(UC_ARM_REG_PC)==checksum+8:
   uc.mem_write(BASE+63,bytes([slot[63]^1]));changed[0]=True
 cpu.cpu.hook_add(UC_HOOK_MEM_READ,read,begin=BASE,end=BASE+63)
 result=cpu.call(entry,BASE)
 rows.append({'role':role,'result':result,'reads':reads,'mutation_applied':changed[0]})
print(json.dumps(rows));Path('/tmp/syscon-slot-read-order-before.json').write_text(json.dumps(rows,indent=2)+'\n')
