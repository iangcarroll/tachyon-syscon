/* UNREVIEWED Ghidra output: FUN_00000c54 @ 00000c54 */

bool FUN_00000c54(uint param_1,uint param_2)

{
  uint uVar1;
  uint uVar2;
  uint uVar3;
  bool bVar4;
  
  uVar3 = param_1 & 0x7fffff;
  uVar1 = (param_1 & 0x7fffffff) >> 0x17;
  uVar2 = (param_2 & 0x7fffffff) >> 0x17;
  if (uVar1 == 0xff) {
    if (uVar3 != 0) {
      return true;
    }
    if (uVar2 != 0xff) {
      return true;
    }
    if ((param_2 & 0x7fffff) != 0) {
      return true;
    }
  }
  else {
    if (uVar2 == 0xff) {
      return true;
    }
    if (uVar1 != uVar2) {
      return true;
    }
    if (uVar3 != (param_2 & 0x7fffff)) {
      return true;
    }
  }
  if (-((int)param_1 >> 0x1f) == -((int)param_2 >> 0x1f)) {
    bVar4 = false;
  }
  else {
    bVar4 = true;
    if (uVar1 == 0) {
      bVar4 = uVar3 != 0;
    }
  }
  return bVar4;
}


