/* UNREVIEWED Ghidra output: FUN_00009450 @ 00009450 */

void FUN_00009450(int param_1,uint param_2,int param_3)

{
  uint *puVar1;
  uint uVar2;
  
  puVar1 = (uint *)(param_1 + DAT_00009468 + param_3 * 4);
  uVar2 = *puVar1;
  *puVar1 = (param_2 ^ uVar2) & DAT_0000946c ^ uVar2;
  return;
}


