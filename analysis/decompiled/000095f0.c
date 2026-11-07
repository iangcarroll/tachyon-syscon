/* UNREVIEWED Ghidra output: FUN_000095f0 @ 000095f0 */

void FUN_000095f0(int param_1,ushort *param_2)

{
  *(uint *)(param_1 + 0x1100) = *(uint *)(param_1 + 0x1100) & 0xfffffffe;
  *(uint *)(param_1 + 0x1100) =
       (((uint)*param_2 | (uint)(byte)param_2[1] | (uint)param_2[2]) ^ *(uint *)(param_1 + 0x1100))
       & DAT_00009630 ^ *(uint *)(param_1 + 0x1100);
  *(uint *)(param_1 + DAT_00009634) =
       ((uint)(byte)((byte)param_2[3] | *(byte *)((int)param_2 + 7) | (byte)param_2[4]) ^
       *(uint *)(param_1 + DAT_00009634)) & 0x7e ^ *(uint *)(param_1 + DAT_00009634);
  return;
}


