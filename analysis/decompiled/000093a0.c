/* UNREVIEWED Ghidra output: FUN_000093a0 @ 000093a0 */

void FUN_000093a0(int param_1)

{
  int iVar1;
  int iVar2;
  
  iVar2 = DAT_000093cc;
  iVar1 = DAT_000093c8;
  *(uint *)(param_1 + DAT_000093c8) = *(uint *)(param_1 + DAT_000093c8) | 0x80;
  do {
  } while ((*(uint *)(param_1 + iVar2) & 0xf00) != 0x800);
  *(uint *)(param_1 + iVar1) = *(uint *)(param_1 + iVar1) & 0xffffff7f;
  return;
}


