/* UNREVIEWED Ghidra output: FUN_000080ac @ 000080ac */

undefined4 FUN_000080ac(uint param_1)

{
  int iVar1;
  int iVar2;
  int *piVar3;
  
  iVar2 = DAT_000080ec;
  if (0x18 < param_1) {
    iVar1 = FUN_000098dc(DAT_000080ec,0x2f);
    if (iVar1 != 0) {
      iVar2 = FUN_000098dc(iVar2,0x2f);
      iVar2 = iVar2 + 1;
    }
    FUN_00002678(iVar2,0x6d,DAT_000080f0);
  }
  piVar3 = (int *)FUN_00007a54(param_1 & 0xff);
  *(int *)(*piVar3 + DAT_000080f4) = 1 << (sbyte)piVar3[1];
  return 0;
}


