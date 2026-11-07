/* UNREVIEWED Ghidra output: FUN_00009012 @ 00009012 */

void FUN_00009012(undefined1 param_1,int *param_2)

{
  uint uVar1;
  
  uVar1 = param_2[2];
  if (uVar1 < (uint)param_2[1]) {
    param_2[2] = uVar1 + 1;
    *(undefined1 *)(*param_2 + uVar1) = param_1;
  }
  return;
}


