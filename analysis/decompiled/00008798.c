/* UNREVIEWED Ghidra output: vector_40 @ 00008798 */

void vector_40(void)

{
  undefined4 uVar1;
  undefined4 uVar2;
  uint uVar3;
  
  uVar1 = DAT_000087d8;
  uVar2 = DAT_000087d0;
  uVar3 = *(uint *)(DAT_000087c8 + 0x1020) & 0xff;
  if (uVar3 == 8) {
    *DAT_000087cc = 1;
  }
  else {
    if (uVar3 != 0xb) {
      return;
    }
    *DAT_000087cc = 1;
    uVar2 = uVar1;
  }
  FUN_00008f88(1,DAT_000087d4,uVar2);
  return;
}


