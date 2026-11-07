/* UNREVIEWED Ghidra output: FUN_000024a8 @ 000024a8 */

int FUN_000024a8(uint param_1,uint param_2,uint param_3,uint param_4)

{
  int iVar1;
  int iVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  
  uVar4 = param_4 & 0xfffff;
  uVar6 = param_2 & 0xfffff;
  uVar3 = (param_2 & 0x7fffffff) >> 0x14;
  iVar2 = -((int)param_2 >> 0x1f);
  uVar5 = (param_4 & 0x7fffffff) >> 0x14;
  iVar1 = -((int)param_4 >> 0x1f);
  if (uVar3 == DAT_00002570) {
    if (uVar6 != 0 || param_1 != 0) {
      return -2;
    }
    if (uVar5 == uVar3) goto LAB_00002502;
LAB_00002524:
    if ((uVar5 == 0) && (param_3 == 0 && uVar4 == 0)) goto LAB_000024f2;
  }
  else if (uVar5 == DAT_00002570) {
LAB_00002502:
    if (param_3 != 0 || uVar4 != 0) {
      return -2;
    }
    if ((uVar3 == 0) && (param_1 == 0 && uVar6 == 0)) goto LAB_00002510;
  }
  else {
    if (uVar3 != 0) goto LAB_00002524;
    if ((uVar5 == 0) && (param_3 == 0 && uVar4 == 0)) {
      if (param_1 == 0 && uVar6 == 0) {
        return 0;
      }
      goto LAB_000024f2;
    }
    if (param_1 == 0 && uVar6 == 0) goto LAB_00002510;
  }
  if (iVar2 == iVar1) {
    if (uVar5 < uVar3) {
      return (uint)(iVar1 == 0) * 2 + -1;
    }
    if (uVar3 < uVar5) {
LAB_00002510:
      if ((int)param_4 < 0) {
        return iVar1;
      }
      return -1;
    }
    if (uVar6 <= uVar4) {
      if (uVar6 == uVar4) {
        if (param_3 < param_1) goto LAB_000024f2;
        if (param_3 <= param_1) {
          return 0;
        }
      }
      else if (uVar4 <= uVar6) {
        return 0;
      }
      if (iVar2 == 0) {
        return -1;
      }
      return iVar2;
    }
  }
LAB_000024f2:
  return (iVar2 - 1U & 2) - 1;
}


