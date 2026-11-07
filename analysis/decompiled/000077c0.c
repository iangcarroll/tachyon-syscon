/* UNREVIEWED Ghidra output: FUN_000077c0 @ 000077c0 */

void FUN_000077c0(uint param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  uint *puVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  
  FUN_00008f88(1,DAT_000077f4,DAT_000077f0,param_1,param_4);
  puVar1 = DAT_000077f8;
  uVar3 = *DAT_000077f8;
  uVar4 = DAT_000077f8[1];
  while( true ) {
    uVar2 = *puVar1;
    if ((puVar1[1] - uVar4 != (uint)(uVar2 < uVar3)) || (param_1 <= uVar2 - uVar3)) break;
    FUN_000079d0();
  }
  return;
}


