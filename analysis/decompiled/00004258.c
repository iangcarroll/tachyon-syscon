/* UNREVIEWED Ghidra output: cmd_560D_ON @ 00004258 */

bool cmd_560D_ON(undefined4 param_1,code *param_2)

{
  int iVar1;
  
  iVar1 = FUN_0000263c(param_1,DAT_000042b4);
  if (iVar1 == 0) {
    iVar1 = FUN_00006428();
  }
  else {
    iVar1 = FUN_0000263c(param_1,DAT_000042b8);
    if (iVar1 == 0) {
      iVar1 = FUN_000065e4();
    }
    else {
      iVar1 = FUN_0000263c(param_1,DAT_000042bc);
      if (iVar1 == 0) {
        iVar1 = FUN_000065d0();
      }
      else {
        iVar1 = FUN_0000263c(param_1,DAT_000042c0);
        if (iVar1 != 0) {
          (*param_2)(DAT_000042c4);
          return false;
        }
        iVar1 = FUN_000064a0();
      }
    }
  }
  return iVar1 == 0;
}


