/* UNREVIEWED Ghidra output: FUN_00008054 @ 00008054 */

undefined4 FUN_00008054(uint param_1,int param_2)

{
  int iVar1;
  int iVar2;
  int *piVar3;
  
  iVar2 = DAT_000080a0;
  if (0x18 < param_1) {
    iVar1 = FUN_000098dc(DAT_000080a0,0x2f);
    if (iVar1 != 0) {
      iVar2 = FUN_000098dc(iVar2,0x2f);
      iVar2 = iVar2 + 1;
    }
    FUN_00002678(iVar2,0x61,DAT_000080a4);
  }
  piVar3 = (int *)FUN_00007a54(param_1 & 0xff);
  if (param_2 == 0) {
    iVar2 = 0x12a0;
  }
  else {
    iVar2 = DAT_000080a8;
  }
  *(int *)(*piVar3 + iVar2) = 1 << (sbyte)piVar3[1];
  return 0;
}


