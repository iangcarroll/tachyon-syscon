/* UNREVIEWED Ghidra output: FUN_0000942c @ 0000942c */

void FUN_0000942c(int param_1,uint param_2,uint param_3,int param_4)

{
  uint uVar1;
  uint *puVar2;
  
  puVar2 = (uint *)(param_1 + DAT_00009448 + param_4 * 4);
  uVar1 = *puVar2;
  *puVar2 = ((param_2 | param_3) ^ uVar1) & DAT_0000944c ^ uVar1;
  return;
}


