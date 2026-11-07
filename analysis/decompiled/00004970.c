/* UNREVIEWED Ghidra output: cmd_KEY_MODE @ 00004970 */

undefined4 cmd_KEY_MODE(undefined4 param_1,code *param_2)

{
  int iVar1;
  undefined4 uVar2;
  
  iVar1 = FUN_0000263c(param_1,PTR_s_DETECT___000049a0);
  if (iVar1 == 0) {
    uVar2 = 1;
  }
  else {
    iVar1 = FUN_0000263c(param_1,PTR_s_PASSTHRU___000049a4);
    uVar2 = 0;
    if (iVar1 != 0) {
      (*param_2)(PTR_s_Invalid_parameters__Use__HELP____000049a8);
      return 0;
    }
  }
  FUN_0000591c(uVar2);
  return 1;
}


