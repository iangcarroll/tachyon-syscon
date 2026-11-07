/* UNREVIEWED Ghidra output: FUN_00004d00 @ 00004d00 */

int FUN_00004d00(void)

{
  int iVar1;
  int iVar2;
  int iVar3;
  
  iVar1 = FUN_00003620(0x23);
  iVar2 = FUN_00003620(0x1a);
  iVar3 = DAT_00004d50;
  if (iVar1 != 1) {
    if (iVar1 != 0) goto LAB_00004d1c;
    if (iVar2 == 1) {
      return 2;
    }
  }
  if (iVar2 == 0) {
    return iVar1;
  }
LAB_00004d1c:
  iVar1 = FUN_000098dc(DAT_00004d50,0x2f);
  if (iVar1 != 0) {
    iVar3 = FUN_000098dc(iVar3,0x2f);
    iVar3 = iVar3 + 1;
  }
  FUN_00002678(iVar3,0x17c,DAT_00004d54);
  return 0;
}


