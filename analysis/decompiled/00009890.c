/* UNREVIEWED Ghidra output: FUN_00009890 @ 00009890 */

int FUN_00009890(int param_1,int param_2,int param_3)

{
  byte *pbVar1;
  uint uVar2;
  int iVar3;
  
  iVar3 = 0;
  if (param_3 != 0) {
    iVar3 = 0;
    do {
      uVar2 = (uint)*(byte *)(param_1 + iVar3);
      pbVar1 = (byte *)(param_2 + iVar3);
      if ((uVar2 != *pbVar1) || (iVar3 == param_3 + -1)) break;
      iVar3 = iVar3 + 1;
    } while (uVar2 != 0);
    iVar3 = uVar2 - *pbVar1;
  }
  return iVar3;
}


