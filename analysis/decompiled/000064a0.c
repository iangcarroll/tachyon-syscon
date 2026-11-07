/* UNREVIEWED Ghidra output: FUN_000064a0 @ 000064a0 */

undefined4 FUN_000064a0(void)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 local_30;
  undefined4 uStack_2c;
  undefined4 uStack_28;
  undefined4 local_24;
  undefined4 uStack_20;
  undefined4 uStack_1c;
  undefined4 local_18;
  undefined4 uStack_14;
  
  if (*DAT_00006504 == '\0') {
    FUN_000055dc(0);
    *DAT_00006510 = 0;
    *DAT_00006514 = 0;
    FUN_00006282();
    FUN_00007928(0);
    local_30 = *(undefined4 *)(DAT_00006518 + 0x18);
    uStack_2c = *(undefined4 *)(DAT_00006518 + 0x1c);
    uStack_28 = *(undefined4 *)(DAT_00006518 + 0x20);
    local_24 = *(undefined4 *)(DAT_00006518 + 0x24);
    uStack_20 = *(undefined4 *)(DAT_00006518 + 0x28);
    uStack_1c = *(undefined4 *)(DAT_00006518 + 0x2c);
    local_18 = *(undefined4 *)(DAT_00006518 + 0x30);
    uStack_14 = *(undefined4 *)(DAT_00006518 + 0x34);
    iVar1 = FUN_00007554(&local_30,4,(int)register0x00000054 + -0x10,DAT_00006518 + 0x38);
    uVar2 = 0;
    if (iVar1 < 0) {
      FUN_00008f88(3,DAT_0000650c,DAT_0000651c);
    }
  }
  else {
    FUN_00008f88(1,DAT_0000650c,DAT_00006508);
    uVar2 = 0xffffffff;
  }
  return uVar2;
}


