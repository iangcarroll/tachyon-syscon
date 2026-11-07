/* UNREVIEWED Ghidra output: FUN_00009470 @ 00009470 */

void FUN_00009470(int param_1,uint param_2,uint param_3,int param_4)

{
  uint uVar1;
  uint *puVar2;
  
  puVar2 = (uint *)(param_1 + 0x1880 + param_4 * 4);
  uVar1 = *puVar2;
  *puVar2 = ((param_2 | param_3) ^ uVar1) & 0x8f ^ uVar1;
  return;
}


