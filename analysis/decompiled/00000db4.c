/* UNREVIEWED Ghidra output: FUN_00000db4 @ 00000db4 */

uint FUN_00000db4(uint param_1,uint param_2)

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  int iVar5;
  int iVar6;
  uint uVar7;
  
  uVar3 = param_1 & 0x7fffff;
  uVar4 = (param_1 & 0x7fffffff) >> 0x17;
  if (uVar4 == 0) {
    if (uVar3 == 0) {
      uVar7 = 4;
      iVar5 = 0;
    }
    else {
      iVar5 = FUN_000023d0(uVar3);
      uVar3 = uVar3 << (iVar5 - 5U & 0xff);
      uVar7 = 0;
      iVar5 = -0x76 - iVar5;
    }
  }
  else if (uVar4 == 0xff) {
    if (uVar3 == 0) {
      uVar7 = 8;
      iVar5 = 0xff;
    }
    else {
      uVar7 = 0xc;
      iVar5 = 0xff;
    }
  }
  else {
    uVar7 = 0;
    uVar3 = uVar3 << 3 | 0x4000000;
    iVar5 = uVar4 - 0x7f;
  }
  uVar4 = param_2 & 0x7fffff;
  uVar2 = (param_2 & 0x7fffffff) >> 0x17;
  if (uVar2 == 0) {
    if (uVar4 == 0) {
      uVar7 = uVar7 | 1;
    }
    else {
      iVar1 = FUN_000023d0(uVar4);
      uVar4 = uVar4 << (iVar1 - 5U & 0xff);
      iVar5 = (iVar5 - iVar1) + -0x76;
    }
  }
  else if (uVar2 == 0xff) {
    iVar5 = iVar5 + 0xff;
    if (uVar4 == 0) {
      uVar7 = uVar7 | 2;
    }
    else {
      uVar7 = uVar7 | 3;
    }
  }
  else {
    iVar5 = iVar5 + (uVar2 - 0x7f);
    uVar4 = uVar4 << 3 | 0x4000000;
  }
  iVar1 = iVar5 + 1;
  if (uVar7 < 0x10) {
                    /* WARNING: Could not recover jumptable at 0x00000e24. Too many branches */
                    /* WARNING: Treating indirect jump as call */
    uVar3 = (**(code **)(DAT_00000ff8 + uVar7 * 4))();
    return uVar3;
  }
  uVar2 = (uVar3 & 0xffff) * (uVar4 & 0xffff);
  uVar7 = (uVar3 >> 0x10) * (uVar4 & 0xffff);
  iVar6 = (uVar4 >> 0x10) * (uVar3 >> 0x10);
  uVar3 = (uVar2 >> 0x10) + (uVar4 >> 0x10) * (uVar3 & 0xffff) + uVar7;
  if (uVar3 < uVar7) {
    iVar6 = iVar6 + 0x10000;
  }
  uVar7 = uVar3 * 0x10000 + (uVar2 & 0xffff);
  uVar4 = (uint)((uVar7 & 0x3ffffff) != 0);
  uVar7 = uVar7 >> 0x1a;
  iVar6 = (uVar3 >> 0x10) + iVar6;
  uVar3 = uVar4 | uVar7 | iVar6 * 0x40;
  if (iVar6 * 0x400 < 0) {
    uVar3 = uVar4 | uVar7 & 1 | uVar3 >> 1;
  }
  else {
    iVar1 = iVar5;
  }
  uVar4 = iVar1 + 0x7f;
  if ((int)uVar4 < 1) {
    if ((int)(1 - uVar4) < 0x1c) {
      uVar4 = uVar3 >> (1 - uVar4 & 0xff);
      uVar3 = (uint)(uVar3 << (iVar1 + 0x9eU & 0xff) != 0);
      uVar7 = uVar3 | uVar4;
      if ((uVar3 != 0 || (uVar4 & 7) != 0) && ((uVar3 | uVar4 & 0xf) != 4)) {
        uVar7 = uVar7 + 4;
      }
      if ((int)(uVar7 << 5) < 0) {
        uVar4 = 1;
        uVar3 = 0;
      }
      else {
        uVar4 = 0;
        uVar3 = (uVar7 & 0x3ffffff) >> 3;
      }
    }
    else {
      uVar4 = 0;
      uVar3 = 0;
    }
  }
  else {
    if (((uVar3 & 7) != 0) && ((uVar3 & 0xf) != 4)) {
      uVar3 = uVar3 + 4;
    }
    if ((int)(uVar3 << 4) < 0) {
      uVar4 = iVar1 + 0x80;
      uVar3 = uVar3 & DAT_00000ffc;
    }
    if ((int)uVar4 < 0xff) {
      uVar3 = (uVar3 & 0x3ffffff) >> 3;
      uVar4 = uVar4 & 0xff;
    }
    else {
      uVar4 = 0xff;
      uVar3 = 0;
    }
  }
  return uVar4 << 0x17 | uVar3 | (param_1 ^ param_2) & 0x80000000;
}


