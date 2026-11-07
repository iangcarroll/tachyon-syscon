/* UNREVIEWED Ghidra output: FUN_00009a40 @ 00009a40 */

int FUN_00009a40(int param_1)

{
  if ((*(byte *)(DAT_00009a50 + param_1) & 3) == 2) {
    param_1 = param_1 + -0x20;
  }
  return param_1;
}


