/* UNREVIEWED Ghidra output: FUN_000051c0 @ 000051c0 */

undefined4 FUN_000051c0(void)

{
  undefined4 *puVar1;
  undefined1 *puVar2;
  int iVar3;
  undefined4 uVar4;
  undefined4 local_28;
  undefined4 uStack_24;
  undefined4 uStack_20;
  undefined4 local_1c;
  undefined4 uStack_18;
  undefined4 uStack_14;
  
  iVar3 = FUN_0000517c();
  if (iVar3 == 0) {
    iVar3 = FUN_00004c50(0x10);
    if (iVar3 <= DAT_00005248) {
      FUN_00008f88(3,DAT_00005244,DAT_0000524c);
      return 0xffffffff;
    }
    iVar3 = FUN_00004ec4();
    puVar2 = DAT_0000525c;
    puVar1 = DAT_00005258;
    if (iVar3 != 0) {
      local_28 = *DAT_00005254;
      uStack_24 = DAT_00005254[1];
      uStack_20 = DAT_00005254[2];
      local_1c = DAT_00005254[3];
      uStack_18 = DAT_00005254[4];
      uStack_14 = DAT_00005254[5];
      *DAT_0000525c = 1;
      *puVar1 = 0;
      puVar1[1] = 0;
      iVar3 = FUN_00007554(&local_28,3);
      if (iVar3 < 0) {
        FUN_00008f88(1,DAT_00005244,DAT_00005260);
        *puVar2 = 0;
        return 0xffffffff;
      }
      return 0;
    }
    uVar4 = DAT_00005250;
  }
  else {
    uVar4 = DAT_00005240;
  }
  FUN_00008f88(2,DAT_00005244,uVar4);
  return 0xffffffff;
}


