/* UNREVIEWED Ghidra output: cmd_SHUTDOWN_REASON @ 000041a4 */

undefined4 cmd_SHUTDOWN_REASON(undefined4 param_1,code *param_2)

{
  int iVar1;
  undefined4 uVar2;
  
  iVar1 = FUN_0000263c(param_1,DAT_00004210);
  if (iVar1 == 0) {
    uVar2 = 1;
  }
  else {
    iVar1 = FUN_0000263c(param_1,PTR_s_POWEROFF___00004214);
    if ((iVar1 == 0) || (iVar1 = FUN_0000263c(param_1,PTR_s_USER___00004218), iVar1 == 0)) {
      uVar2 = 2;
    }
    else {
      iVar1 = FUN_0000263c(param_1,PTR_s_BATTERY_LOW___0000421c);
      uVar2 = 3;
      if (iVar1 != 0) {
        iVar1 = FUN_0000263c(param_1,PTR_s_THERMAL_HIGH___00004220);
        uVar2 = 4;
        if (iVar1 != 0) {
          iVar1 = FUN_0000263c(param_1,PTR_s_THERMAL_LOW___00004224);
          uVar2 = 5;
          if (iVar1 != 0) {
            (*param_2)(PTR_s_Invalid_parameters__Use__HELP____00004228);
            return 0;
          }
        }
      }
    }
  }
  FUN_000055dc(uVar2);
  return 1;
}


