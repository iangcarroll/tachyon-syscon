/* UNREVIEWED Ghidra output: FUN_00005aa8 @ 00005aa8 */

void FUN_00005aa8(byte param_1)

{
  *(byte *)(DAT_00005ac0 + 1) = *(byte *)(DAT_00005ac0 + 1) & 0xf0 | param_1 & 0xf;
  FUN_000059a0();
  return;
}


