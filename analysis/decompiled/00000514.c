/* UNREVIEWED Ghidra output: FUN_00000514 @ 00000514 */

int FUN_00000514(undefined4 param_1,undefined4 param_2)

{
  int iVar1;
  
  iVar1 = FUN_000023bc(param_1,param_2,0,DAT_0000054c);
  if (iVar1 == 0) {
    iVar1 = FUN_00002258(param_1,param_2);
  }
  else {
    FUN_00001b34(param_1,param_2,0,DAT_0000054c);
    iVar1 = FUN_00002258();
    iVar1 = iVar1 + -0x80000000;
  }
  return iVar1;
}


