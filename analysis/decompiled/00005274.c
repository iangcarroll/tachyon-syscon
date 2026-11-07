/* UNREVIEWED Ghidra output: FUN_00005274 @ 00005274 */

int FUN_00005274(void)

{
  undefined4 uVar1;
  int iVar2;
  int iVar3;
  
  iVar2 = FUN_00004c50(0xe);
  uVar1 = DAT_00005334;
  if (DAT_00005330 < iVar2) {
    FUN_00008f88(3,DAT_00005334,DAT_00005354,iVar2);
    iVar2 = 1;
  }
  else {
    iVar2 = FUN_00004e34(2);
    if (iVar2 < 0) {
      FUN_00008f88(1,uVar1,DAT_00005338);
    }
    FUN_00004e04(1);
    iVar2 = FUN_00005264(0);
    if (iVar2 < 0) {
      FUN_00008f88(1,uVar1,DAT_0000533c);
    }
    iVar2 = FUN_00004c50(0x17);
    FUN_00008f88(3,uVar1,DAT_00005340,iVar2);
    iVar3 = FUN_00004e34(0);
    if (iVar3 < 0) {
      FUN_00008f88(1,uVar1,DAT_00005344);
    }
    iVar3 = FUN_00005264(1);
    iVar2 = (800 < iVar2 - 400U) + 1;
    if (iVar3 < 0) {
      FUN_00008f88(1,uVar1,DAT_00005348,iVar3);
    }
  }
  FUN_00008f88(3,uVar1,DAT_00005350,*(undefined4 *)(iVar2 * 4 + DAT_0000534c));
  FUN_00005ad4(iVar2);
  FUN_00004e04(0);
  return iVar2;
}


