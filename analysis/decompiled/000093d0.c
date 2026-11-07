/* UNREVIEWED Ghidra output: FUN_000093d0 @ 000093d0 */

void FUN_000093d0(int param_1)

{
  int iVar1;
  
  iVar1 = DAT_000093f4;
  *(uint *)(param_1 + DAT_000093f4) = *(uint *)(param_1 + DAT_000093f4) | 0x8000;
  do {
  } while ((*(uint *)(param_1 + DAT_000093f8) & 0xf) != 0);
  *(uint *)(param_1 + iVar1) = *(uint *)(param_1 + iVar1) & DAT_000093fc;
  return;
}


