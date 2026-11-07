/* UNREVIEWED Ghidra output: FUN_00007f24 @ 00007f24 */

int FUN_00007f24(void)

{
  int iVar1;
  
  iVar1 = FUN_00007e7c();
  if (-1 < iVar1) {
    iVar1 = *(int *)(DAT_00007f54 + 0xb) * iVar1;
    iVar1 = (int)((iVar1 >> 0x1f & 0xfffU) + iVar1) >> 0xc;
  }
  return iVar1;
}


