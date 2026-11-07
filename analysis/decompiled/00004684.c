/* UNREVIEWED Ghidra output: cmd_CONFIG_ID_SET @ 00004684 */

int cmd_CONFIG_ID_SET(undefined4 param_1,code *param_2)

{
  int iVar1;
  undefined1 auStack_50 [32];
  undefined1 auStack_30 [36];
  
  iVar1 = FUN_000097d4(param_1,PTR_DAT_000046c4,auStack_50,auStack_30);
  if (iVar1 == 2) {
    iVar1 = FUN_00003278(auStack_50,auStack_30);
    if (iVar1 == 0) {
      (*param_2)(PTR_s_Refused___s_000046cc,auStack_50);
    }
    else {
      (*param_2)(PTR_s__s____s_0000b942_7_000046c8,auStack_50,auStack_30);
    }
  }
  else {
    (*param_2)(PTR_s_Invalid_parameters__Use__HELP____000046d0);
    iVar1 = 0;
  }
  return iVar1;
}


