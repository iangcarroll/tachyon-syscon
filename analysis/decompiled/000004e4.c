/* UNREVIEWED Ghidra output: FUN_000004e4 @ 000004e4 */

int FUN_000004e4(undefined4 param_1)

{
  int iVar1;
  
  iVar1 = FUN_00000434(param_1,0x4f000000);
  if (iVar1 == 0) {
    iVar1 = FUN_0000135c(param_1);
  }
  else {
    FUN_00001000(param_1,0x4f000000);
    iVar1 = FUN_0000135c();
    iVar1 = iVar1 + -0x80000000;
  }
  return iVar1;
}


