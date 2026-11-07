/* UNREVIEWED Ghidra output: FUN_00002f0c @ 00002f0c */

undefined4 FUN_00002f0c(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  uint uVar2;
  undefined4 uVar3;
  undefined4 local_1c [2];
  
  iVar1 = FUN_00002810(param_3);
  if ((iVar1 == 0) || (iVar1 = FUN_00002810(param_4), iVar1 == 0)) {
    FUN_00008f88(1,DAT_00002f94,DAT_00002f90,param_3);
  }
  else {
    uVar2 = FUN_00002650(param_3);
    if ((uVar2 < 0x1f) && (uVar2 = FUN_00002650(param_4), uVar2 < 0x1f)) {
      local_1c[0] = 0;
      iVar1 = FUN_000029a0(param_1,param_2,param_3,0,local_1c);
      if (iVar1 == 0) {
        FUN_00008f88(1,DAT_00002f94,DAT_00002f98);
        return 0;
      }
      uVar3 = FUN_000028d4(local_1c[0],param_3,param_4);
      return uVar3;
    }
    FUN_00008f88(1,DAT_00002f94,DAT_00002f9c);
  }
  return 0;
}


