/* UNREVIEWED Ghidra output: FUN_000080f8 @ 000080f8 */

bool FUN_000080f8(uint param_1)

{
  int iVar1;
  int iVar2;
  int *piVar3;
  
  iVar2 = DAT_00008140;
  if (0x18 < param_1) {
    iVar1 = FUN_000098dc(DAT_00008140,0x2f);
    if (iVar1 != 0) {
      iVar2 = FUN_000098dc(iVar2,0x2f);
      iVar2 = iVar2 + 1;
    }
    FUN_00002678(iVar2,0x74,DAT_00008144);
  }
  piVar3 = (int *)FUN_00007a54(param_1 & 0xff);
  return (*(uint *)(*piVar3 + 0x1380) & 1 << (sbyte)piVar3[1]) != 0;
}


