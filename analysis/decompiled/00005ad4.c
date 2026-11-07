/* UNREVIEWED Ghidra output: FUN_00005ad4 @ 00005ad4 */

void FUN_00005ad4(char param_1)

{
  *(byte *)(DAT_00005aec + 1) = *(byte *)(DAT_00005aec + 1) & 0xf | param_1 << 4;
  FUN_000059a0();
  return;
}


