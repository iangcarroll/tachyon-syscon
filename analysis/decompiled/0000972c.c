/* UNREVIEWED Ghidra output: FUN_0000972c @ 0000972c */

int FUN_0000972c(int param_1,int param_2,int param_3)

{
  byte *pbVar1;
  int iVar2;
  uint uVar3;
  
  iVar2 = 0;
  do {
    if (param_3 == iVar2) {
      return 0;
    }
    pbVar1 = (byte *)(param_1 + iVar2);
    iVar2 = iVar2 + 1;
    uVar3 = (uint)*(byte *)(param_2 + -1 + iVar2);
  } while (*pbVar1 == uVar3);
  return *pbVar1 - uVar3;
}


