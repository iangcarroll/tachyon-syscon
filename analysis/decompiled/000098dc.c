/* UNREVIEWED Ghidra output: FUN_000098dc @ 000098dc */

int FUN_000098dc(int param_1,int param_2)

{
  int iVar1;
  int iVar2;
  
  iVar1 = 0;
  if (param_2 == 0) {
    iVar1 = FUN_00009828(param_1,0);
  }
  else {
    while (iVar2 = FUN_00009828(param_1,param_2), iVar2 != 0) {
      param_1 = iVar2 + 1;
      iVar1 = iVar2;
    }
  }
  return iVar1;
}


