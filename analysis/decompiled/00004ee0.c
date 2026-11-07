/* UNREVIEWED Ghidra output: FUN_00004ee0 @ 00004ee0 */

longlong FUN_00004ee0(uint param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  undefined4 uVar1;
  int iVar2;
  undefined4 uVar3;
  uint uVar4;
  undefined4 uVar5;
  int iVar6;
  uint uVar7;
  
  uVar1 = DAT_00004fac;
  uVar7 = param_1;
  FUN_00008f88(3,DAT_00004fac,DAT_00004fb0,param_4,param_1,param_2,param_3);
  FUN_00004ed4(1);
  FUN_000077c0(0x14);
  iVar2 = FUN_00004c50(0xd);
  if (iVar2 <= DAT_00004fb4) {
    FUN_00008f88(1,uVar1,DAT_00004fb8,iVar2,uVar7,param_2,param_3);
  }
  if (param_1 == 1) {
    FUN_00008f88(3,uVar1,DAT_00004fbc);
    FUN_0000364e(0x19,0);
    uVar5 = 1;
  }
  else {
    if (param_1 == 2) {
      FUN_00008f88(3,uVar1,DAT_00004fc0);
      FUN_0000364e(0x28,0);
      uVar5 = 1;
      uVar3 = 0x19;
      goto LAB_00004f4a;
    }
    FUN_000077c0(0x14);
    FUN_0000364e(0x19,0);
    uVar5 = 0;
  }
  uVar3 = 0x28;
LAB_00004f4a:
  FUN_0000364e(uVar3,uVar5);
  uVar4 = FUN_00004d9c();
  if (uVar4 != param_1) {
    uVar5 = FUN_00004d9c();
    uVar7 = param_1;
    FUN_00008f88(1,uVar1,DAT_00004fc4,uVar5);
  }
  uVar4 = FUN_00004d9c();
  iVar2 = DAT_00004fc8;
  if (uVar4 != param_1) {
    iVar6 = FUN_000098dc(DAT_00004fc8,0x2f);
    if (iVar6 != 0) {
      iVar2 = FUN_000098dc(iVar2,0x2f);
      iVar2 = iVar2 + 1;
    }
    FUN_00002678(iVar2,0x1e6,DAT_00004fcc);
  }
  return (ulonglong)uVar7 << 0x20;
}


