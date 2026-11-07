/* UNREVIEWED Ghidra output: FUN_0000aa88 @ 0000aa88 */

void FUN_0000aa88(int *param_1,undefined4 param_2)

{
  int *piVar1;
  int iVar2;
  
  piVar1 = DAT_0000aaa8;
  *DAT_0000aaa8 = 0;
  iVar2 = FUN_000076f0(param_2);
  if ((iVar2 == -1) && (*piVar1 != 0)) {
    *param_1 = *piVar1;
  }
  return;
}


