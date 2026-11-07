/* UNREVIEWED Ghidra output: FUN_00002738 @ 00002738 */

void FUN_00002738(void)

{
  undefined4 uVar1;
  uint uVar2;
  
  uVar2 = *(uint *)(DAT_0000277c + DAT_00002780) & DAT_00002784;
  uVar1 = DAT_0000278c;
  if (uVar2 == 0x40) goto LAB_00002774;
  if (uVar2 < 0x41) {
    uVar1 = DAT_00002790;
    if (((uVar2 == 0x10) || (uVar1 = DAT_00002794, uVar2 == 0x20)) ||
       (uVar1 = DAT_00002798, uVar2 == 0)) goto LAB_00002774;
  }
  else {
    uVar1 = DAT_000027a0;
    if (uVar2 == 0x80) goto LAB_00002774;
    if (uVar2 == 0x1000) {
      uVar1 = DAT_000027a4;
      goto LAB_00002774;
    }
  }
  uVar1 = DAT_0000279c;
LAB_00002774:
  FUN_00008f88(1,DAT_00002788,uVar1);
  return;
}


