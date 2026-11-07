/* UNREVIEWED Ghidra output: FUN_00002258 @ 00002258 */

uint FUN_00002258(uint param_1,uint param_2)

{
  uint uVar1;
  uint uVar2;
  uint uVar3;
  
  uVar3 = (param_2 & 0x7fffffff) >> 0x14;
  uVar1 = 0;
  if (DAT_000022ac < (int)uVar3) {
    if (DAT_000022b0 < (int)uVar3) {
      uVar1 = DAT_000022b4 - ((int)param_2 >> 0x1f);
    }
    else {
      uVar2 = param_2 & 0xfffff | 0x100000;
      if ((int)(DAT_000022b8 - uVar3) < 0x20) {
        uVar2 = uVar2 << (uVar3 + DAT_000022c0 & 0xff) | param_1 >> (DAT_000022b8 - uVar3 & 0xff);
      }
      else {
        uVar2 = uVar2 >> (DAT_000022bc - uVar3 & 0xff);
      }
      uVar1 = -uVar2;
      if (-1 < (int)param_2) {
        uVar1 = uVar2;
      }
    }
  }
  return uVar1;
}


