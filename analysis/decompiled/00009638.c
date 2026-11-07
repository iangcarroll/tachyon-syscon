/* UNREVIEWED Ghidra output: FUN_00009638 @ 00009638 */

void FUN_00009638(int param_1,byte *param_2)

{
  int iVar1;
  
  iVar1 = DAT_00009648;
  *(uint *)(param_1 + DAT_00009648) = (uint)*param_2;
  *(uint *)(param_1 + iVar1 + -8) = (uint)param_2[1];
  return;
}


