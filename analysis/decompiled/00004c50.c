/* UNREVIEWED Ghidra output: FUN_00004c50 @ 00004c50 */

int FUN_00004c50(uint param_1)

{
  int iVar1;
  uint uVar2;
  int iVar3;
  
  iVar1 = FUN_00007f24(param_1 & 0xffff);
  if (iVar1 == 0) {
    iVar1 = FUN_00007f24(param_1 & 0xffff);
  }
  if (param_1 == 0xc) {
    iVar3 = 0;
  }
  else if (param_1 == 0xd) {
    iVar3 = 1;
  }
  else if (param_1 == 0xe) {
    iVar3 = 2;
  }
  else if (param_1 == 0xf) {
    iVar3 = 3;
  }
  else if (param_1 == 0x10) {
    iVar3 = 4;
  }
  else {
    uVar2 = 0;
    if (param_1 != 0x17) goto LAB_00004c8a;
    iVar3 = 5;
  }
  uVar2 = (uint)*(byte *)(DAT_00004ca4 + iVar3 * 2 + 1);
LAB_00004c8a:
  return uVar2 * iVar1;
}


