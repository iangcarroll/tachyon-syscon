/* UNREVIEWED Ghidra output: FUN_00009844 @ 00009844 */

undefined8 FUN_00009844(int param_1,int param_2,int param_3)

{
  int iVar1;
  uint uVar2;
  int iVar3;
  uint uVar4;
  
  iVar3 = 0;
  do {
    if (iVar3 == param_3) {
      iVar1 = 0;
      break;
    }
    uVar4 = (uint)*(byte *)(param_1 + iVar3);
    if ((*(byte *)(DAT_0000988c + uVar4) & 3) == 1) {
      uVar4 = uVar4 + 0x20;
    }
    uVar2 = (uint)*(byte *)(param_2 + iVar3);
    if ((*(byte *)(DAT_0000988c + uVar2) & 3) == 1) {
      uVar2 = uVar2 + 0x20;
    }
    iVar1 = uVar4 - uVar2;
    if (uVar4 != uVar2) break;
    iVar3 = iVar3 + 1;
    iVar1 = 0;
  } while (uVar2 != 0);
  return CONCAT44(param_1,iVar1);
}


