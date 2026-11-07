/* UNREVIEWED Ghidra output: cmd_560D_OFF @ 000048a4 */

undefined4 cmd_560D_OFF(undefined4 param_1,code *param_2)

{
  int iVar1;
  undefined4 uVar2;
  
  iVar1 = FUN_0000263c(param_1,PTR_s_SOFT___000048d4);
  uVar2 = 0;
  if (iVar1 != 0) {
    iVar1 = FUN_0000263c(param_1,PTR_s_HARD___000048d8);
    if (iVar1 != 0) {
      (*param_2)(PTR_s_Invalid_parameters__Use__HELP____000048dc);
      return 0;
    }
    uVar2 = 1;
  }
  uVar2 = FUN_00006720(uVar2);
  return uVar2;
}


