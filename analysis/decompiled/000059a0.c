/* UNREVIEWED Ghidra output: FUN_000059a0 @ 000059a0 */

undefined8 FUN_000059a0(undefined4 param_1,undefined4 param_2)

{
  int iVar1;
  byte local_c;
  byte local_b;
  byte local_a;
  undefined1 uStack_9;
  
  local_c = (byte)param_2;
  local_b = (byte)((uint)param_2 >> 8);
  local_a = (byte)((uint)param_2 >> 0x10);
  uStack_9 = (undefined1)((uint)param_2 >> 0x18);
  FUN_00009748(&local_c,DAT_000059c8,3);
  iVar1 = DAT_000059cc;
  *(uint *)(DAT_000059cc + 0x1400) = (uint)local_c;
  *(uint *)(iVar1 + DAT_000059d0) = (uint)local_b;
  *(uint *)(iVar1 + DAT_000059d4) = (uint)local_a;
  return CONCAT17(uStack_9,CONCAT16(local_a,CONCAT15(local_b,CONCAT14(local_c,param_1))));
}


