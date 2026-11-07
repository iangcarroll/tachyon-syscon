/* UNREVIEWED Ghidra output: FUN_00003098 @ 00003098 */

undefined4 FUN_00003098(uint param_1)

{
  int iVar1;
  
  if (param_1 < 0xf) {
    iVar1 = 0;
    do {
      if (*(char *)(param_1 * 0x40 + DAT_000030bc + iVar1) != -1) {
        return 0;
      }
      iVar1 = iVar1 + 1;
    } while (iVar1 != 0x40);
  }
  return 1;
}


