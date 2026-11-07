/* UNREVIEWED Ghidra output: cmd_KEYS @ 00004850 */

undefined4 cmd_KEYS(undefined4 param_1,code *param_2)

{
  int iVar1;
  undefined4 uVar2;
  
  iVar1 = FUN_0000263c(param_1,PTR_s_UP___00004894);
  uVar2 = 0x27;
  if (iVar1 != 0) {
    iVar1 = FUN_0000263c(param_1,PTR_s_DOWN___00004898);
    if (iVar1 == 0) {
      uVar2 = 0x1d;
    }
    else {
      iVar1 = FUN_0000263c(param_1,PTR_s_POWER___0000489c);
      uVar2 = 8;
      if (iVar1 != 0) {
        (*param_2)(PTR_s_Invalid_parameters__Use__HELP____000048a0);
        return 0;
      }
    }
  }
  FUN_00007468(uVar2);
  return 1;
}


