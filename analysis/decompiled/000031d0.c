/* UNREVIEWED Ghidra output: FUN_000031d0 @ 000031d0 */

undefined4 FUN_000031d0(undefined4 param_1)

{
  undefined4 uVar1;
  undefined4 uVar2;
  int iVar3;
  int iVar4;
  undefined4 uVar5;
  undefined1 auStack_30 [32];
  
  iVar3 = FUN_0000263c(param_1,DAT_00003254);
  uVar1 = DAT_00003260;
  if (iVar3 == 0) {
    iVar3 = FUN_000027a8(DAT_00003260,0x400);
    uVar2 = DAT_00003264;
    uVar5 = 0;
    if (iVar3 != 0) {
      uVar5 = FUN_00002f0c(uVar1,0x400,DAT_00003264,DAT_00003268);
      iVar3 = FUN_00002cb8(uVar1,0x400,uVar2,auStack_30);
      if (iVar3 == 0) {
        FUN_00008f88(1,DAT_0000325c,DAT_0000326c);
        iVar3 = DAT_00003270;
        iVar4 = FUN_000098dc(DAT_00003270,0x2f);
        if (iVar4 != 0) {
          iVar3 = FUN_000098dc(iVar3,0x2f);
          iVar3 = iVar3 + 1;
        }
        FUN_00002678(iVar3,0x3a4,DAT_00003274);
      }
    }
  }
  else {
    FUN_00008f88(1,DAT_0000325c,DAT_00003258);
    uVar5 = 0;
  }
  return uVar5;
}


