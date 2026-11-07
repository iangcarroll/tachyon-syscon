/* UNREVIEWED Ghidra output: FUN_00009664 @ 00009664 */

void FUN_00009664(int param_1,byte *param_2)

{
  *(uint *)(param_1 + 0x1100) = (uint)(*param_2 | param_2[1]) | (uint)*(ushort *)(param_2 + 2);
  *(uint *)(param_1 + DAT_00009684) = *(int *)(param_2 + 8) << 0x10 | *(uint *)(param_2 + 4);
  return;
}


