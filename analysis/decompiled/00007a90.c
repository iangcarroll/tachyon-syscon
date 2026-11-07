/* UNREVIEWED Ghidra output: FUN_00007a90 @ 00007a90 */

byte * FUN_00007a90(uint param_1)

{
  int iVar1;
  
  if (*DAT_00007abc == param_1) {
    iVar1 = 0;
  }
  else if (DAT_00007abc[0xc] == param_1) {
    iVar1 = 1;
  }
  else {
    if (DAT_00007abc[0x18] != param_1) {
      return (byte *)0x0;
    }
    iVar1 = 2;
  }
  return DAT_00007abc + iVar1 * 0xc;
}


