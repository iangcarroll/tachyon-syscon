/* UNREVIEWED Ghidra output: FUN_00005004 @ 00005004 */

int FUN_00005004(int param_1)

{
  int iVar1;
  int iVar2;
  undefined4 uVar3;
  
  uVar3 = DAT_00005038;
  if (param_1 != 0) {
    uVar3 = DAT_0000503c;
  }
  FUN_00008f88(3,DAT_00005044,DAT_00005040,uVar3);
  iVar1 = FUN_0000364e(0x20,'\x01' - (param_1 == 0));
  iVar2 = FUN_0000364e(0x1c,param_1 == 0);
  return iVar1 + iVar2;
}


