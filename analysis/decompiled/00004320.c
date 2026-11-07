/* UNREVIEWED Ghidra output: cmd_SET_PATTERN @ 00004320 */

bool cmd_SET_PATTERN(undefined4 param_1,code *param_2)

{
  uint uVar1;
  int iVar2;
  int iVar3;
  bool bVar4;
  
  uVar1 = FUN_000096aa();
  iVar2 = FUN_00009828(param_1,0x3a);
  iVar3 = 0;
  if (iVar2 != 0) {
    iVar3 = FUN_000096aa(iVar2 + 1);
  }
  if ((uVar1 < 10) && (-1 < iVar3)) {
    iVar2 = FUN_00005c68(uVar1 & 0xff);
    bVar4 = iVar2 == 0;
  }
  else {
    (*param_2)(DAT_00004360);
    bVar4 = false;
  }
  return bVar4;
}


