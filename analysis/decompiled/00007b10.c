/* UNREVIEWED Ghidra output: FUN_00007b10 @ 00007b10 */

void FUN_00007b10(int param_1,undefined4 param_2,undefined4 *param_3)

{
  int iVar1;
  
  *(undefined4 *)(param_1 + DAT_00007b34) = 1;
  iVar1 = DAT_00007b38;
  *(undefined4 *)(param_1 + DAT_00007b38) = 0xff;
  *(undefined4 *)(param_1 + iVar1 + -4) = param_2;
  *(undefined4 *)(param_1 + DAT_00007b3c) = *param_3;
  *(undefined4 *)(param_1 + DAT_00007b40) = param_3[1];
  FUN_0000aae0();
  return;
}


