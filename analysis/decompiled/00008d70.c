/* UNREVIEWED Ghidra output: FUN_00008d70 @ 00008d70 */

void FUN_00008d70(int param_1)

{
  int iVar1;
  int iVar2;
  undefined4 uVar3;
  
  iVar1 = FUN_00007ac0(0);
  if (param_1 != *(int *)(iVar1 + 8)) {
    iVar1 = 0;
  }
  iVar2 = FUN_00007ac0(1);
  if (param_1 == *(int *)(iVar2 + 8)) {
    iVar2 = 1;
  }
  else {
    iVar2 = 0;
    if (iVar1 == 0) {
      return;
    }
  }
  if ((*(uint *)(param_1 + 0x1020) & 0xff) == 0xb) {
    uVar3 = *(undefined4 *)(param_1 + DAT_00008ddc);
    iVar1 = FUN_00008cf0(iVar2);
    if (iVar1 != 0x40) {
      iVar1 = DAT_00008de0 + iVar2 * 0x4c;
      *(char *)(iVar1 + *(int *)(iVar1 + 0x40)) = (char)uVar3;
      *(uint *)(iVar1 + 0x40) = *(int *)(iVar1 + 0x40) + 1U & 0x3f;
      if (*(int *)(iVar1 + 0x40) == *(int *)(iVar1 + 0x44)) {
        *(undefined1 *)(iVar1 + 0x48) = 1;
      }
    }
  }
  return;
}


