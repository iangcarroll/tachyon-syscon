/* UNREVIEWED Ghidra output: FUN_00005f30 @ 00005f30 */

undefined8 FUN_00005f30(undefined4 param_1,undefined4 param_2,undefined4 param_3)

{
  bool bVar1;
  undefined4 uVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  uint uVar7;
  undefined4 uVar8;
  longlong lVar9;
  
  iVar3 = FUN_00005274();
  iVar4 = FUN_00004ca8();
  uVar2 = DAT_000060e8;
  FUN_00008f88(3,DAT_000060e8,DAT_000060f0,*(undefined4 *)(iVar4 * 4 + DAT_000060ec),param_1,param_2
               ,param_3);
  iVar5 = FUN_00004c50(0xf);
  if (DAT_000060f4 < iVar5) {
    FUN_00008f88(1,uVar2,DAT_000060f8,DAT_000060f4,param_1,param_2,param_3);
    iVar5 = DAT_000060fc;
    iVar6 = FUN_000098dc(DAT_000060fc,0x2f);
    if (iVar6 != 0) {
      iVar5 = FUN_000098dc(iVar5,0x2f);
      iVar5 = iVar5 + 1;
    }
    FUN_00002678(iVar5,0x152,DAT_00006100);
  }
  iVar6 = FUN_00003194();
  iVar5 = DAT_000060fc;
  if (iVar6 == 0) {
    if (iVar4 != 0) {
      iVar4 = FUN_000098dc(DAT_000060fc,0x2f);
      if (iVar4 != 0) {
        iVar5 = FUN_000098dc(iVar5,0x2f);
        iVar5 = iVar5 + 1;
      }
      FUN_00002678(iVar5,0x159,DAT_00006134);
    }
  }
  else if (iVar4 != 0) {
    FUN_00008f88(1,uVar2,DAT_00006104);
  }
  uVar7 = FUN_00004d9c();
  iVar4 = FUN_00004c50(0xd);
  iVar5 = FUN_00004c50(0xe);
  if ((DAT_00006108 < iVar4) && (uVar7 < 2)) {
    FUN_00008f88(3,uVar2,DAT_0000610c);
    bVar1 = true;
  }
  else {
    FUN_00008f88(3,uVar2,DAT_00006138);
    bVar1 = false;
  }
  iVar4 = FUN_00004c50(0x10);
  if (iVar4 <= DAT_00006110) {
    FUN_00008f88(2,uVar2,DAT_00006114,iVar4);
  }
  if (bVar1) {
    iVar6 = FUN_00004ee0(1);
    uVar8 = DAT_00006118;
    if (iVar6 < 0) {
LAB_00006098:
      FUN_00008f88(1,uVar2,uVar8);
    }
  }
  else {
    iVar6 = FUN_00004ee0(2);
    if (iVar6 < 0) {
      uVar8 = DAT_0000613c;
      goto LAB_00006098;
    }
  }
  if (iVar3 == 1) {
    if (iVar5 < 2000) {
      iVar5 = FUN_00003194();
      if (iVar5 != 0) {
        FUN_00008f88(1,uVar2,DAT_00006140);
        iVar5 = FUN_00004e34(2);
        if (iVar5 < 0) {
          FUN_00008f88(1,uVar2,DAT_00006144);
        }
        *DAT_00006148 = 1;
      }
      goto LAB_00006012;
    }
    iVar5 = FUN_00004e34(1);
    uVar8 = DAT_0000611c;
    if (-1 < iVar5) goto LAB_00006012;
  }
  else {
    iVar5 = FUN_00004e34(2);
    if (-1 < iVar5) goto LAB_00006012;
    uVar8 = DAT_00006144;
  }
  FUN_00008f88(1,uVar2,uVar8);
LAB_00006012:
  if (((DAT_00006110 < iVar4) || (!bVar1)) || (uVar8 = 2, iVar3 != 1)) {
    uVar8 = 1;
  }
  FUN_00005048(uVar8);
  FUN_00005358(DAT_00006120);
  *DAT_00006124 = 1;
  lVar9 = FUN_000077b4();
  uVar8 = DAT_00006130;
  *DAT_0000612c = lVar9 + (ulonglong)DAT_00006128;
  FUN_00008f88(3,uVar2,uVar8);
  return CONCAT44(param_1,1);
}


