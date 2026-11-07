/* UNREVIEWED Ghidra output: FUN_00003940 @ 00003940 */

undefined8 FUN_00003940(uint param_1,uint param_2)

{
  int iVar1;
  int iVar2;
  undefined4 uVar3;
  undefined4 uStack_14;
  
  iVar2 = DAT_000039d4;
  uStack_14 = param_2;
  if (*DAT_000039d0 == '\0') {
    iVar1 = FUN_000098dc(DAT_000039d4,0x2f);
    if (iVar1 != 0) {
      iVar2 = FUN_000098dc(iVar2,0x2f);
      iVar2 = iVar2 + 1;
    }
    FUN_00002678(iVar2,0x8d,DAT_000039d8);
  }
  iVar2 = DAT_000039d4;
  if (0xf < param_1) {
    iVar1 = FUN_000098dc(DAT_000039d4,0x2f);
    if (iVar1 != 0) {
      iVar2 = FUN_000098dc(iVar2,0x2f);
      iVar2 = iVar2 + 1;
    }
    FUN_00002678(iVar2,0x8e,DAT_000039dc);
  }
  FUN_000036bc((param_1 >> 3) + 6,(int)&uStack_14 + 3);
  if ((uStack_14 >> 0x18 & 1 << (param_1 & 7)) == 0) {
    uVar3 = FUN_0000379c(param_1,param_2);
  }
  else {
    FUN_00008f88(1,DAT_000039e4,DAT_000039e0,param_1);
    uVar3 = 0xffffffff;
  }
  return CONCAT44(param_1,uVar3);
}


