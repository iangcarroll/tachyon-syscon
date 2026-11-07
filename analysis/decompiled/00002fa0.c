/* UNREVIEWED Ghidra output: FUN_00002fa0 @ 00002fa0 */

void FUN_00002fa0(undefined4 param_1,undefined4 param_2)

{
  undefined4 uVar1;
  undefined4 uVar2;
  int iVar3;
  int iVar4;
  undefined1 auStack_38 [36];
  
  uVar1 = DAT_00003024;
  iVar3 = FUN_00002cb8(param_1,param_2,DAT_00003024,auStack_38);
  uVar2 = DAT_00003028;
  if (iVar3 == 0) {
    FUN_00008f88(3,DAT_00003028,DAT_0000302c,param_1);
    FUN_000027a8(param_1,param_2);
    FUN_00002f0c(param_1,param_2,uVar1,DAT_00003030);
    iVar3 = FUN_00002cb8(param_1,param_2,uVar1,auStack_38);
    if (iVar3 == 0) {
      FUN_00008f88(1,uVar2,DAT_00003034);
      iVar3 = DAT_00003038;
      iVar4 = FUN_000098dc(DAT_00003038,0x2f);
      if (iVar4 != 0) {
        iVar3 = FUN_000098dc(iVar3,0x2f);
        iVar3 = iVar3 + 1;
      }
      FUN_00002678(iVar3,DAT_00003040,DAT_0000303c);
    }
  }
  else {
    FUN_00008f88(3,DAT_00003028,DAT_00003044,param_1);
  }
  return;
}


