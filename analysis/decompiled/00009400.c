/* UNREVIEWED Ghidra output: FUN_00009400 @ 00009400 */

void FUN_00009400(int param_1,byte *param_2)

{
  int iVar1;
  
  iVar1 = DAT_00009414;
  *(uint *)(param_1 + DAT_00009414) = (uint)*param_2;
  *(uint *)(param_1 + iVar1 + -8) = (uint)param_2[1];
  *(uint *)(param_1 + DAT_00009418) = (uint)param_2[2];
  return;
}


