/* UNREVIEWED Ghidra output: cmd_WAKE_AFTER @ 000040a0 */

undefined8 cmd_WAKE_AFTER(int param_1,code *param_2,undefined4 param_3)

{
  int iVar1;
  undefined4 uVar2;
  code *local_14;
  undefined4 uStack_10;
  
  uStack_10 = param_3;
  if (param_1 == 0) {
    local_14 = param_2;
    iVar1 = FUN_00006650();
    if (iVar1 < 0) {
      (*param_2)(PTR_s_Timed_wake__none_000040e8);
    }
    else {
      (*param_2)(PTR_s_Timed_wake__in__ds_000040ec);
    }
    uVar2 = 1;
  }
  else {
    local_14 = (code *)0x0;
    iVar1 = FUN_000097d4(param_1,DAT_000040f0,&local_14);
    if (iVar1 == 1) {
      if (local_14 <= DAT_000040f8) {
        FUN_000065f0();
        uVar2 = 1;
        goto LAB_000040b6;
      }
    }
    (*param_2)(DAT_000040f4);
    uVar2 = 0;
  }
LAB_000040b6:
  return CONCAT44(param_1,uVar2);
}


