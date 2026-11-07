/* UNREVIEWED Ghidra output: FUN_00002d08 @ 00002d08 */

void FUN_00002d08(undefined4 param_1,undefined4 param_2,undefined1 *param_3)

{
  int iVar1;
  undefined1 uVar2;
  undefined4 local_30;
  undefined1 auStack_2c [28];
  
  local_30 = 0;
  FUN_0000975a(auStack_2c,0,0x1c);
  iVar1 = FUN_00002cb8(param_1,0x3c0,param_2,&local_30);
  if (iVar1 != 0) {
    iVar1 = FUN_0000263c(&local_30,DAT_00002d7c);
    if ((iVar1 == 0) || (iVar1 = FUN_0000263c(&local_30,DAT_00002d80), iVar1 == 0)) {
      uVar2 = 1;
    }
    else {
      iVar1 = FUN_0000263c(&local_30,DAT_00002d84);
      if ((iVar1 != 0) && (iVar1 = FUN_0000263c(&local_30,DAT_00002d88), iVar1 != 0)) {
        FUN_00008f88(1,DAT_00002d90,DAT_00002d8c,param_2);
        return;
      }
      uVar2 = 0;
    }
    *param_3 = uVar2;
  }
  return;
}


