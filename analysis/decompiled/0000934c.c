/* UNREVIEWED Ghidra output: FUN_0000934c @ 0000934c */

void FUN_0000934c(int param_1,byte *param_2)

{
  int iVar1;
  uint uVar2;
  
  iVar1 = DAT_00009370;
  *(uint *)(param_1 + DAT_00009370) =
       ((uint)*param_2 ^ *(uint *)(param_1 + DAT_00009370)) & 0xc ^
       *(uint *)(param_1 + DAT_00009370);
  uVar2 = *(uint *)(param_1 + iVar1 + -4);
  *(uint *)(param_1 + iVar1 + -4) = (param_2[1] ^ uVar2) & 7 ^ uVar2;
  return;
}


