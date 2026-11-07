/* UNREVIEWED Ghidra output: FUN_00000448 @ 00000448 */

void FUN_00000448(int param_1,int param_2,int param_3,int param_4)

{
  if ((param_4 != 0) || (param_3 != 0)) {
    FUN_00000550(param_1);
    return;
  }
  if (param_2 != 0 || param_1 != 0) {
    param_2 = -1;
    param_1 = -1;
  }
                    /* WARNING: Could not recover jumptable at 0x00000468. Too many branches */
                    /* WARNING: Treating indirect jump as call */
  (*(code *)(DAT_0000046c + 0x46c))(param_1,param_2);
  return;
}


