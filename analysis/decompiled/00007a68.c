/* UNREVIEWED Ghidra output: FUN_00007a68 @ 00007a68 */

int FUN_00007a68(uint param_1)

{
  int iVar1;
  
  iVar1 = 0;
  do {
    if (*(byte *)(iVar1 * 0xc + DAT_00007a8c) == param_1) {
      return DAT_00007a8c + iVar1 * 0xc;
    }
    iVar1 = iVar1 + 1;
  } while (iVar1 != 6);
  return 0;
}


