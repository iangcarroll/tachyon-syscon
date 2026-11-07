/* UNREVIEWED Ghidra output: FUN_000022c4 @ 000022c4 */

undefined8 FUN_000022c4(uint param_1)

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  
  uVar2 = (param_1 & 0x7fffffff) >> 0x17;
  uVar3 = param_1 & 0x7fffff;
  if ((uVar2 + 1 & 0xfe) == 0) {
    if (uVar2 == 0) {
      if (uVar3 == 0) {
        uVar4 = 0;
        uVar2 = 0;
      }
      else {
        iVar1 = FUN_000023d0(uVar3);
        if (iVar1 < 0xb) {
          uVar4 = uVar3 >> (0xbU - iVar1 & 0xff);
          uVar3 = uVar3 << (iVar1 + 0x15U & 0xff);
        }
        else {
          uVar4 = uVar3 << (iVar1 - 0xbU & 0xff);
          uVar3 = 0;
        }
        uVar4 = uVar4 & 0xfffff;
        uVar2 = DAT_0000234c - iVar1 & 0x7ff;
      }
    }
    else {
      uVar2 = DAT_00002350;
      if (uVar3 == 0) {
        uVar4 = 0;
      }
      else {
        uVar3 = param_1 << 0x1d;
        uVar4 = (param_1 & 0x7fffff) >> 3 | 0x80000;
      }
    }
  }
  else {
    uVar3 = param_1 << 0x1d;
    uVar4 = (param_1 & 0x7fffff) >> 3;
    uVar2 = uVar2 + 0x380;
  }
  return CONCAT44(uVar2 << 0x14 | uVar4 | param_1 & 0x80000000,uVar3);
}


