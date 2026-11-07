/* UNREVIEWED Ghidra output: FUN_00000a24 @ 00000a24 */

uint FUN_00000a24(uint param_1,uint param_2)

{
  uint uVar1;
  uint uVar2;
  int iVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  int iVar7;
  uint uVar8;
  bool bVar9;
  
  uVar5 = param_1 & 0x7fffff;
  uVar6 = (param_1 & 0x7fffffff) >> 0x17;
  if (uVar6 == 0) {
    if (uVar5 == 0) {
      uVar8 = 4;
      iVar7 = 0;
    }
    else {
      iVar7 = FUN_000023d0(uVar5);
      uVar5 = uVar5 << (iVar7 - 5U & 0xff);
      uVar8 = 0;
      iVar7 = -0x76 - iVar7;
    }
  }
  else if (uVar6 == 0xff) {
    if (uVar5 == 0) {
      uVar8 = 8;
      iVar7 = 0xff;
    }
    else {
      uVar8 = 0xc;
      iVar7 = 0xff;
    }
  }
  else {
    uVar5 = uVar5 << 3 | 0x4000000;
    uVar8 = 0;
    iVar7 = uVar6 - 0x7f;
  }
  uVar6 = param_2 & 0x7fffff;
  uVar2 = (param_2 & 0x7fffffff) >> 0x17;
  if (uVar2 == 0) {
    if (uVar6 == 0) {
      uVar5 = 1;
LAB_00000b0c:
      uVar2 = (param_1 ^ param_2) >> 0x1f;
      if ((uVar8 | uVar5) < 0x10) {
                    /* WARNING: Could not recover jumptable at 0x00000b20. Too many branches */
                    /* WARNING: Treating indirect jump as call */
        uVar5 = (**(code **)(DAT_00000c50 + (uVar8 | uVar5) * 4))();
        return uVar5;
      }
      uVar5 = 0xff;
      uVar6 = 0;
      goto LAB_00000ae6;
    }
    iVar3 = FUN_000023d0(uVar6);
    uVar6 = uVar6 << (iVar3 - 5U & 0xff);
    iVar3 = -0x76 - iVar3;
    uVar1 = 0;
  }
  else if (uVar2 == 0xff) {
    if (uVar6 == 0) {
      uVar5 = 2;
      goto LAB_00000b0c;
    }
    iVar3 = 0xff;
    uVar1 = 3;
  }
  else {
    uVar6 = uVar6 << 3 | 0x4000000;
    uVar1 = 0;
    iVar3 = uVar2 - 0x7f;
  }
  iVar7 = iVar7 - iVar3;
  uVar2 = (param_1 ^ param_2) >> 0x1f;
  if ((uVar8 | uVar1) < 0x10) {
                    /* WARNING: Could not recover jumptable at 0x00000a92. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    uVar5 = (**(code **)(DAT_00000c48 + (uVar8 | uVar1) * 4))();
    return uVar5;
  }
  uVar5 = uVar5 * 0x20;
  uVar8 = uVar6 * 0x20;
  bVar9 = uVar8 <= uVar5;
  if (bVar9) {
    iVar3 = 0x1a;
    uVar5 = uVar5 + uVar6 * -0x20;
  }
  else {
    iVar3 = 0x1b;
    iVar7 = iVar7 + -1;
  }
  uVar1 = (uint)bVar9;
  do {
    uVar1 = uVar1 << 1;
    uVar4 = uVar5 * 2;
    if (((int)uVar5 < 0) || (uVar8 <= uVar4)) {
      uVar4 = uVar4 + uVar6 * -0x20;
      uVar1 = uVar1 | 1;
    }
    iVar3 = iVar3 + -1;
    uVar5 = uVar4;
  } while (iVar3 != 0);
  uVar6 = (uint)(uVar4 != 0);
  uVar8 = uVar1 | uVar6;
  uVar5 = iVar7 + 0x7f;
  if ((int)uVar5 < 1) {
    if ((int)(1 - uVar5) < 0x1c) {
      uVar6 = uVar8 >> (1 - uVar5 & 0xff);
      uVar5 = (uint)(uVar8 << (iVar7 + 0x9eU & 0xff) != 0);
      uVar8 = uVar5 | uVar6;
      if ((uVar5 != 0 || (uVar6 & 7) != 0) && ((uVar5 | uVar6 & 0xf) != 4)) {
        uVar8 = uVar8 + 4;
      }
      if ((int)(uVar8 << 5) < 0) {
        uVar5 = 1;
        uVar6 = 0;
      }
      else {
        uVar5 = 0;
        uVar6 = (uVar8 & 0x3ffffff) >> 3;
      }
    }
    else {
      uVar5 = 0;
      uVar6 = 0;
    }
  }
  else {
    if (((uVar1 & 7) != 0 || uVar6 != 0) && ((uVar1 & 0xf | uVar6) != 4)) {
      uVar8 = uVar8 + 4;
    }
    if ((int)(uVar8 << 4) < 0) {
      uVar8 = uVar8 & DAT_00000c4c;
      uVar5 = iVar7 + 0x80;
    }
    if ((int)uVar5 < 0xff) {
      uVar6 = (uVar8 & 0x3ffffff) >> 3;
      uVar5 = uVar5 & 0xff;
    }
    else {
      uVar5 = 0xff;
      uVar6 = 0;
    }
  }
LAB_00000ae6:
  return uVar5 << 0x17 | uVar6 | uVar2 << 0x1f;
}


