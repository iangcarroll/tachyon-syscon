/* UNREVIEWED Ghidra output: FUN_000027a8 @ 000027a8 */

undefined4 FUN_000027a8(int param_1,uint param_2)

{
  int iVar1;
  uint uVar2;
  
  uVar2 = 0;
  do {
    FUN_00007b44(DAT_000027d8);
    iVar1 = FUN_00007af4(DAT_000027d8,param_1 + uVar2,0x40);
    if (iVar1 != 3) {
      FUN_00002738();
      return 0;
    }
    uVar2 = uVar2 + 0x40;
  } while (uVar2 < param_2);
  return 1;
}


