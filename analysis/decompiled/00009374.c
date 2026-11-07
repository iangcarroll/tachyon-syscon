/* UNREVIEWED Ghidra output: FUN_00009374 @ 00009374 */

void FUN_00009374(int param_1,int param_2,uint param_3)

{
  byte *pbVar1;
  uint uVar2;
  
  uVar2 = 0;
  while (((uVar2 & 0xffff) < param_3 && ((*(uint *)(param_1 + DAT_0000939c) & 0xf00) != 0))) {
    pbVar1 = (byte *)(param_2 + uVar2);
    uVar2 = uVar2 + 1;
    *(uint *)(param_1 + 0x1220) = (uint)*pbVar1;
  }
  return;
}


