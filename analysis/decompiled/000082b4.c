/* UNREVIEWED Ghidra output: FUN_000082b4 @ 000082b4 */

undefined4 FUN_000082b4(int param_1,undefined4 param_2)

{
  undefined4 uVar1;
  
  uVar1 = FUN_00007b9c(param_2);
  FUN_00008f88(1,DAT_000082e4,DAT_000082e8,uVar1);
  *(undefined4 *)(*(int *)(param_1 + 4) + DAT_000082ec) = 0;
  FUN_000093a0();
  FUN_000093d0(*(undefined4 *)(param_1 + 4));
  return 0xffffffff;
}


