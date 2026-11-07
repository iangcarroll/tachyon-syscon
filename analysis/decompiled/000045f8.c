/* UNREVIEWED Ghidra output: cmd_CONFIG_ID_ERASE @ 000045f8 */

int cmd_CONFIG_ID_ERASE(undefined4 param_1,code *param_2)

{
  int iVar1;
  undefined *puVar2;
  undefined1 auStack_30 [36];
  
  iVar1 = FUN_000097d4(param_1,DAT_00004628,auStack_30);
  if (iVar1 == 1) {
    iVar1 = FUN_000031d0(auStack_30);
    puVar2 = DAT_0000462c;
    if (iVar1 == 0) {
      puVar2 = PTR_s_Invalid_password_00004630;
    }
    (*param_2)(puVar2);
  }
  else {
    (*param_2)(PTR_s_Invalid_parameters__Use__HELP____00004634);
    iVar1 = 0;
  }
  return iVar1;
}


