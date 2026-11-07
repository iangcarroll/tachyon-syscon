/* UNREVIEWED Ghidra output: FUN_0000aa3c @ 0000aa3c */

int FUN_0000aa3c(undefined4 param_1,int param_2,uint param_3,undefined4 param_4)

{
  int iVar1;
  uint uVar2;
  
  if (param_2 == 0) {
    iVar1 = FUN_0000a980(param_1,param_3,param_3,param_4,param_4);
  }
  else if (param_3 == 0) {
    FUN_0000a8ec();
    iVar1 = 0;
  }
  else {
    uVar2 = FUN_0000aacc();
    iVar1 = param_2;
    if ((uVar2 < param_3) && (iVar1 = FUN_0000a980(param_1,param_3), iVar1 != 0)) {
      FUN_00009748(iVar1,param_2,param_3);
      FUN_0000a8ec(param_1,param_2);
    }
  }
  return iVar1;
}


