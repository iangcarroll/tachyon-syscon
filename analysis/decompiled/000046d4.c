/* UNREVIEWED Ghidra output: cmd_CONFIG_ERASE @ 000046d4 */

int cmd_CONFIG_ERASE(undefined4 param_1,code *param_2)

{
  int iVar1;
  undefined *puVar2;
  undefined1 auStack_30 [36];
  
  iVar1 = FUN_000097d4(param_1,PTR_s__31______00004704,auStack_30);
  if (iVar1 == 1) {
    iVar1 = FUN_000033b4(auStack_30);
    puVar2 = PTR_s_Erased_00004708;
    if (iVar1 == 0) {
      puVar2 = PTR_s_Invalid_password_0000470c;
    }
    (*param_2)(puVar2);
  }
  else {
    (*param_2)(PTR_s_Invalid_parameters__Use__HELP____00004710);
    iVar1 = 0;
  }
  return iVar1;
}


