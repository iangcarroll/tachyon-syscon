/* UNREVIEWED Ghidra output: FUN_00003048 @ 00003048 */

undefined4 FUN_00003048(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  uint uVar1;
  undefined4 uVar2;
  int iVar3;
  undefined4 local_1c [2];
  
  uVar1 = FUN_00002650(param_3);
  if (uVar1 < 0x1f) {
    local_1c[0] = 0;
    iVar3 = FUN_000029a0(param_1,param_2,param_3,2,local_1c);
    uVar2 = 0;
    if (iVar3 != 0) {
      uVar2 = FUN_0000296c(local_1c[0],param_4);
    }
  }
  else {
    FUN_00008f88(1,PTR_s_CONF_00003094,PTR_s_Key_too_long_00003090);
    uVar2 = 0;
  }
  return uVar2;
}


