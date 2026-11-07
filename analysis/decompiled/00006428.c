/* UNREVIEWED Ghidra output: FUN_00006428 @ 00006428 */

undefined4 FUN_00006428(void)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 local_28;
  undefined4 uStack_24;
  undefined4 uStack_20;
  undefined4 local_1c;
  undefined4 uStack_18;
  undefined4 uStack_14;
  
  if (*DAT_00006484 == '\0') {
    FUN_000055dc(0);
    *DAT_00006490 = 0;
    *DAT_00006494 = 0;
    FUN_00006282();
    FUN_00007928(0);
    local_28 = *DAT_00006498;
    uStack_24 = DAT_00006498[1];
    uStack_20 = DAT_00006498[2];
    local_1c = DAT_00006498[3];
    uStack_18 = DAT_00006498[4];
    uStack_14 = DAT_00006498[5];
    iVar1 = FUN_00007554(&local_28,3,(int)register0x00000054 + -0x10,DAT_00006498 + 6);
    uVar2 = 0;
    if (iVar1 < 0) {
      FUN_00008f88(3,DAT_0000648c,DAT_0000649c);
    }
  }
  else {
    FUN_00008f88(1,DAT_0000648c,DAT_00006488);
    uVar2 = 0xffffffff;
  }
  return uVar2;
}


