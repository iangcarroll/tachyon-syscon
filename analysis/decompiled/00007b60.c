/* UNREVIEWED Ghidra output: FUN_00007b60 @ 00007b60 */

void FUN_00007b60(int param_1,undefined4 param_2)

{
  int iVar1;
  
  iVar1 = DAT_00007b74;
  *(undefined4 *)(param_1 + DAT_00007b74) = 6;
  *(undefined4 *)(param_1 + iVar1 + 0x1c) = param_2;
  FUN_0000aae0();
  return;
}


