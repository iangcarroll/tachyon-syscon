/* UNREVIEWED Ghidra output: cmd_CONFIG_FIND @ 000044dc */

int cmd_CONFIG_FIND(undefined4 param_1,code *param_2)

{
  int iVar1;
  undefined1 auStack_50 [32];
  undefined1 auStack_30 [36];
  
  iVar1 = FUN_000097d4(param_1,PTR_s__31______00004518,auStack_50);
  if (iVar1 == 1) {
    iVar1 = FUN_00003464(auStack_50,auStack_30);
    if (iVar1 == 0) {
      (*param_2)(PTR_s_Not_found___s_00004520,auStack_50);
    }
    else {
      (*param_2)(PTR_s_Found___s____s_0000451c,auStack_50,auStack_30);
    }
  }
  else {
    (*param_2)(PTR_s_Invalid_parameters__Use__HELP____00004524);
    iVar1 = 0;
  }
  return iVar1;
}


