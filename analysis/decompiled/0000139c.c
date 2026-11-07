/* UNREVIEWED Ghidra output: FUN_0000139c @ 0000139c */

uint FUN_0000139c(uint param_1)

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  
  if (param_1 == 0) {
    param_1 = 0;
    uVar3 = 0;
    uVar4 = 0;
  }
  else {
    uVar4 = param_1 + ((int)param_1 >> 0x1f) ^ (int)param_1 >> 0x1f;
    param_1 = param_1 >> 0x1f;
    iVar1 = FUN_000023d0(uVar4);
    uVar3 = 0x9e - iVar1;
    if ((int)uVar3 < 0x97) {
      if (8 < iVar1) {
        uVar4 = uVar4 << (iVar1 - 8U & 0xff);
      }
      uVar4 = uVar4 & 0x7fffff;
      uVar3 = uVar3 & 0xff;
    }
    else {
      if (0x99 < (int)uVar3) {
        uVar4 = uVar4 >> (5U - iVar1 & 0xff) | (uint)(uVar4 << (iVar1 + 0x1bU & 0xff) != 0);
      }
      if (5 < iVar1) {
        uVar4 = uVar4 << (iVar1 - 5U & 0xff);
      }
      uVar2 = uVar4 & DAT_00001434;
      if ((((uVar4 & 7) != 0) && ((uVar4 & 0xf) != 4)) &&
         (uVar2 = uVar2 + 4, (int)(uVar2 * 0x20) < 0)) {
        uVar2 = uVar2 & DAT_00001434;
        uVar3 = 0x9f - iVar1;
      }
      uVar4 = (uVar2 & 0x3ffffff) >> 3;
      uVar3 = uVar3 & 0xff;
    }
  }
  return uVar3 << 0x17 | uVar4 | param_1 << 0x1f;
}


