/* UNREVIEWED Ghidra output: FUN_000096d4 @ 000096d4 */

void FUN_000096d4(void)

{
  int iVar1;
  int iVar2;
  int iVar3;
  
  iVar1 = DAT_0000970c;
  iVar2 = DAT_00009710 - DAT_0000970c;
  for (iVar3 = 0; iVar3 != iVar2 >> 2; iVar3 = iVar3 + 1) {
    (**(code **)(iVar1 + iVar3 * 4))();
  }
  FUN_00007a50();
  iVar1 = DAT_00009714;
  iVar2 = DAT_00009718 - DAT_00009714;
  for (iVar3 = 0; iVar3 != iVar2 >> 2; iVar3 = iVar3 + 1) {
    (**(code **)(iVar1 + iVar3 * 4))();
  }
  return;
}


