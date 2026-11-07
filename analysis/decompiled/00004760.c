/* UNREVIEWED Ghidra output: cmd_CONFIG_SET @ 00004760 */

int cmd_CONFIG_SET(undefined4 param_1,code *param_2)

{
  int iVar1;
  undefined1 auStack_50 [32];
  undefined1 auStack_30 [36];
  
  iVar1 = FUN_000097d4(param_1,DAT_000047a0,auStack_50,auStack_30);
  if (iVar1 == 2) {
    iVar1 = FUN_000032c8(auStack_50,auStack_30);
    if (iVar1 == 0) {
      (*param_2)(DAT_000047a8,auStack_50);
    }
    else {
      (*param_2)(DAT_000047a4,auStack_50,auStack_30);
    }
  }
  else {
    (*param_2)(DAT_000047ac);
    iVar1 = 0;
  }
  return iVar1;
}


