/* UNREVIEWED Ghidra output: FUN_00004d9c @ 00004d9c */

int FUN_00004d9c(void)

{
  int iVar1;
  int iVar2;
  int iVar3;
  
  iVar1 = FUN_00003620(0x28);
  iVar2 = FUN_00003620(0x19);
  iVar3 = DAT_00004dec;
  if (iVar1 != 1) {
    if (iVar1 != 0) goto LAB_00004db8;
    if (iVar2 == 1) {
      return 2;
    }
  }
  if (iVar2 == 0) {
    return iVar1;
  }
LAB_00004db8:
  iVar1 = FUN_000098dc(DAT_00004dec,0x2f);
  if (iVar1 != 0) {
    iVar3 = FUN_000098dc(iVar3,0x2f);
    iVar3 = iVar3 + 1;
  }
  FUN_00002678(iVar3,0x1a2,DAT_00004df0);
  return 0;
}


