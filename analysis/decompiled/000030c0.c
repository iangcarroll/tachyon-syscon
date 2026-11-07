/* UNREVIEWED Ghidra output: FUN_000030c0 @ 000030c0 */

undefined4 FUN_000030c0(uint param_1)

{
  int iVar1;
  
  if (param_1 < 0x10) {
    iVar1 = 0;
    do {
      if (*(char *)(param_1 * 0x40 + DAT_000030e4 + iVar1) != -1) {
        return 0;
      }
      iVar1 = iVar1 + 1;
    } while (iVar1 != 0x40);
  }
  return 1;
}


