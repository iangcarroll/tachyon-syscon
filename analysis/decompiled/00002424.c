/* UNREVIEWED Ghidra output: FUN_00002424 @ 00002424 */

bool FUN_00002424(int param_1,uint param_2,int param_3,uint param_4)

{
  bool bVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  
  uVar4 = param_2 & 0xfffff;
  uVar3 = (param_2 & 0x7fffffff) >> 0x14;
  uVar2 = (param_4 & 0x7fffffff) >> 0x14;
  if (uVar3 == DAT_000024a4) {
    if (uVar4 != 0 || param_1 != 0) {
      return true;
    }
    if (uVar2 != uVar3) {
      return true;
    }
    if ((param_4 & 0xfffff) != 0 || param_3 != 0) {
      return true;
    }
  }
  else {
    if (uVar2 == DAT_000024a4) {
      return true;
    }
    if (uVar3 != uVar2) {
      return true;
    }
    if (uVar4 != (param_4 & 0xfffff)) {
      return true;
    }
  }
  bVar1 = true;
  if (param_1 == param_3) {
    if (-((int)param_2 >> 0x1f) == -((int)param_4 >> 0x1f)) {
      bVar1 = false;
    }
    else if (uVar3 == 0) {
      bVar1 = uVar4 != 0 || param_1 != 0;
    }
  }
  return bVar1;
}


