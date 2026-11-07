/* UNREVIEWED Ghidra output: FUN_0000930c @ 0000930c */

void FUN_0000930c(int param_1,byte *param_2)

{
  *(uint *)(param_1 + DAT_00009340) =
       ((*param_2 | 0xa9000000) ^ *(uint *)(param_1 + DAT_00009340)) & DAT_00009344 ^
       *(uint *)(param_1 + DAT_00009340);
  *(uint *)(param_1 + 0x1100) =
       (*(uint *)(param_2 + 4) ^ *(uint *)(param_1 + 0x1100)) & 0x7000000 ^
       *(uint *)(param_1 + 0x1100);
  *(uint *)(param_1 + DAT_00009348) = (uint)param_2[1];
  return;
}


