/* UNREVIEWED Ghidra output: FUN_00001438 @ 00001438 */

uint FUN_00001438(uint param_1)

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  
  if (param_1 == 0) {
    uVar3 = 0;
    param_1 = 0;
  }
  else {
    iVar1 = FUN_000023d0();
    uVar3 = 0x9e - iVar1;
    if ((int)uVar3 < 0x97) {
      if (8 < iVar1) {
        param_1 = param_1 << (iVar1 - 8U & 0xff);
      }
      param_1 = param_1 & 0x7fffff;
      uVar3 = uVar3 & 0xff;
    }
    else {
      if (0x99 < (int)uVar3) {
        param_1 = param_1 >> (5U - iVar1 & 0xff) | (uint)(param_1 << (iVar1 + 0x1bU & 0xff) != 0);
      }
      if (5 < iVar1) {
        param_1 = param_1 << (iVar1 - 5U & 0xff);
      }
      uVar2 = param_1 & DAT_000014b8;
      if ((((param_1 & 7) != 0) && ((param_1 & 0xf) != 4)) &&
         (uVar2 = uVar2 + 4, (int)(uVar2 * 0x20) < 0)) {
        uVar2 = uVar2 & DAT_000014b8;
        uVar3 = 0x9f - iVar1;
      }
      param_1 = (uVar2 & 0x3ffffff) >> 3;
      uVar3 = uVar3 & 0xff;
    }
  }
  return uVar3 << 0x17 | param_1;
}


