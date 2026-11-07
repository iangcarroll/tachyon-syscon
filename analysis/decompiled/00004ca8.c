/* UNREVIEWED Ghidra output: FUN_00004ca8 @ 00004ca8 */

int FUN_00004ca8(void)

{
  int iVar1;
  int iVar2;
  int iVar3;
  
  iVar1 = FUN_00003620(0x21);
  iVar2 = FUN_00003620(0x22);
  iVar3 = DAT_00004cf8;
  if (iVar1 != 1) {
    if (iVar1 != 0) goto LAB_00004cc4;
    if (iVar2 == 1) {
      return 2;
    }
  }
  if (iVar2 == 0) {
    return iVar1;
  }
LAB_00004cc4:
  iVar1 = FUN_000098dc(DAT_00004cf8,0x2f);
  if (iVar1 != 0) {
    iVar3 = FUN_000098dc(iVar3,0x2f);
    iVar3 = iVar3 + 1;
  }
  FUN_00002678(iVar3,0x131,DAT_00004cfc);
  return 0;
}


