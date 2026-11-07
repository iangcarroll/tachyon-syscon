/* UNREVIEWED Ghidra output: cmd_CONFIG_ID_FIND @ 00004490 */

int cmd_CONFIG_ID_FIND(undefined4 param_1,code *param_2)

{
  int iVar1;
  undefined1 auStack_50 [32];
  undefined1 auStack_30 [36];
  
  iVar1 = FUN_000097d4(param_1,PTR_s__31______000044cc,auStack_50);
  if (iVar1 == 1) {
    iVar1 = FUN_000032b0(auStack_50,auStack_30);
    if (iVar1 == 0) {
      (*param_2)(PTR_s_Not_found___s_000044d4,auStack_50);
    }
    else {
      (*param_2)(PTR_s_Found___s____s_000044d0,auStack_50,auStack_30);
    }
  }
  else {
    (*param_2)(PTR_s_Invalid_parameters__Use__HELP____000044d8);
    iVar1 = 0;
  }
  return iVar1;
}


