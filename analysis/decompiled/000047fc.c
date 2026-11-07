/* UNREVIEWED Ghidra output: cmd_560D_DBG @ 000047fc */

undefined4 cmd_560D_DBG(undefined4 param_1,code *param_2)

{
  int iVar1;
  undefined *puVar2;
  
  iVar1 = FUN_0000263c(param_1,DAT_00004838);
  puVar2 = DAT_00004840;
  if (iVar1 == 0) {
    *DAT_0000483c = 1;
  }
  else {
    iVar1 = FUN_0000263c(param_1,DAT_00004844);
    if (iVar1 != 0) {
      (*param_2)(PTR_s_Invalid_parameters__Use__HELP____0000484c);
      return 0;
    }
    *DAT_0000483c = 0;
    puVar2 = PTR_s_Debug_disabled_00004848;
  }
  (*param_2)(puVar2);
  return 1;
}


