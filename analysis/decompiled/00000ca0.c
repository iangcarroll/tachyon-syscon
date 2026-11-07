/* UNREVIEWED Ghidra output: FUN_00000ca0 @ 00000ca0 */

int FUN_00000ca0(uint param_1,uint param_2)

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  
  uVar4 = param_1 & 0x7fffff;
  uVar2 = (param_1 & 0x7fffffff) >> 0x17;
  uVar5 = param_2 & 0x7fffff;
  uVar3 = (param_2 & 0x7fffffff) >> 0x17;
  iVar1 = -((int)param_2 >> 0x1f);
  if (uVar2 == 0xff) {
    if (uVar4 != 0) {
      return -2;
    }
    if (uVar3 == 0xff) goto LAB_00000cdc;
LAB_00000cfa:
    if ((uVar3 == 0) && (uVar5 == 0)) goto LAB_00000cd2;
  }
  else {
    if (uVar3 == 0xff) {
LAB_00000cdc:
      if (uVar5 != 0) {
        return -2;
      }
      if (uVar2 != 0) goto LAB_00000cce;
    }
    else {
      if (uVar2 != 0) goto LAB_00000cfa;
      if ((uVar3 == 0) && (uVar5 == 0)) {
        if (uVar4 == 0) {
          return 0;
        }
        goto LAB_00000cd2;
      }
    }
    if (uVar4 == 0) goto LAB_00000ce8;
  }
LAB_00000cce:
  if (-((int)param_1 >> 0x1f) != iVar1) {
LAB_00000cd2:
    return (-((int)param_1 >> 0x1f) - 1U & 2) - 1;
  }
  if (uVar3 < uVar2) {
LAB_00000d1c:
    return (uint)(iVar1 == 0) * 2 + -1;
  }
  if (uVar3 <= uVar2) {
    if (uVar5 < uVar4) goto LAB_00000d1c;
    if (uVar5 <= uVar4) {
      return 0;
    }
  }
LAB_00000ce8:
  if ((int)param_2 < 0) {
    return iVar1;
  }
  return -1;
}


