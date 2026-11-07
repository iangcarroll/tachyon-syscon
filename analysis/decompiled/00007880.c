/* UNREVIEWED Ghidra output: FUN_00007880 @ 00007880 */

void FUN_00007880(int param_1)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  
  iVar1 = DAT_000078a8;
  iVar4 = 0;
  iVar3 = DAT_000078a8;
  do {
    iVar2 = iVar1 + iVar4 * 0x18;
    if (*(int *)(iVar2 + 0x10) == param_1) {
      *(undefined4 *)(iVar2 + 0x10) = 0;
      *(undefined4 *)(iVar3 + 0x14) = 0;
    }
    iVar4 = iVar4 + 1;
    iVar3 = iVar3 + 0x18;
  } while (iVar4 != 4);
  return;
}


