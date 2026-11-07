/* UNREVIEWED Ghidra output: FUN_000065f0 @ 000065f0 */

void FUN_000065f0(int param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  uint *puVar1;
  undefined *puVar2;
  undefined *puVar3;
  longlong lVar4;
  longlong lVar5;
  
  puVar1 = DAT_00006640;
  if (param_1 == 0) {
    if ((*DAT_00006640 | DAT_00006640[1]) != 0) {
      FUN_00008f88(3,PTR_s_560D_00006648,DAT_00006644,*DAT_00006640 | DAT_00006640[1],param_4);
    }
    *puVar1 = 0;
    puVar1[1] = 0;
  }
  else {
    lVar4 = FUN_000077b4();
    lVar5 = FUN_00000488(param_1,0,1000,0);
    puVar3 = PTR_s_Timed_wake_armed___ds_from_now_0000664c;
    puVar2 = PTR_s_560D_00006648;
    *(longlong *)puVar1 = lVar4 + lVar5;
    FUN_00008f88(3,puVar2,puVar3,param_1,param_4);
  }
  return;
}


