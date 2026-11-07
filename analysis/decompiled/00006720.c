/* UNREVIEWED Ghidra output: FUN_00006720 @ 00006720 */

undefined4 FUN_00006720(int param_1)

{
  undefined4 uVar1;
  undefined4 *puVar2;
  int iVar3;
  undefined4 uVar4;
  longlong lVar5;
  
  iVar3 = FUN_000076d8();
  if (iVar3 != 0) {
    FUN_00008f88(3,DAT_00006800,DAT_000067fc);
    return 0;
  }
  iVar3 = FUN_00004c50(0xf);
  uVar1 = DAT_00006800;
  if ((iVar3 <= DAT_00006804) && (param_1 == 0)) goto LAB_000067ae;
  FUN_00008f88(3,DAT_00006800,DAT_00006808);
  iVar3 = FUN_00005048(0);
  if (iVar3 < 0) {
    FUN_00008f88(1,uVar1,DAT_0000680c);
  }
  iVar3 = FUN_00004e34(0);
  if (iVar3 < 0) {
    FUN_00008f88(1,uVar1,DAT_00006810);
  }
  iVar3 = FUN_00003150();
  if (iVar3 == 0) {
    iVar3 = FUN_00004ee0();
    if (iVar3 < 0) {
      FUN_00008f88(1,uVar1,DAT_00006830);
    }
    iVar3 = FUN_00004ed4(0);
    if (iVar3 < 0) {
      uVar4 = DAT_00006834;
      goto LAB_000067f2;
    }
  }
  else {
    iVar3 = FUN_00004fd0();
    uVar4 = DAT_00006814;
    if (iVar3 < 0) {
LAB_000067f2:
      FUN_00008f88(1,uVar1,uVar4);
    }
  }
  FUN_000066bc(1);
  *DAT_00006818 = 3;
  lVar5 = FUN_000077b4();
  *DAT_00006820 = lVar5 + (ulonglong)DAT_0000681c;
LAB_000067ae:
  FUN_00005e30();
  FUN_00006248();
  FUN_00007928(1);
  *DAT_00006824 = 0;
  *DAT_00006828 = 0;
  puVar2 = DAT_0000682c;
  *DAT_0000682c = 0;
  puVar2[1] = 0;
  return 1;
}


