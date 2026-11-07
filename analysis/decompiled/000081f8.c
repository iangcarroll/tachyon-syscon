/* UNREVIEWED Ghidra output: FUN_000081f8 @ 000081f8 */

void FUN_000081f8(uint param_1)

{
  int iVar1;
  int iVar2;
  int *piVar3;
  
  iVar2 = DAT_00008248;
  if (0x18 < param_1) {
    iVar1 = FUN_000098dc(DAT_00008248,0x2f);
    if (iVar1 != 0) {
      iVar2 = FUN_000098dc(iVar2,0x2f);
      iVar2 = iVar2 + 1;
    }
    FUN_00002678(iVar2,0x9b,DAT_0000824c);
  }
  piVar3 = (int *)FUN_00007a54(param_1 & 0xff);
  iVar1 = DAT_00008250;
  iVar2 = piVar3[1];
  *(undefined4 *)(param_1 * 8 + DAT_00008250) = 0;
  *(undefined4 *)(iVar1 + param_1 * 8 + 4) = 0;
  *(uint *)(*piVar3 + DAT_00008254) = *(uint *)(*piVar3 + DAT_00008254) & ~(1 << (sbyte)iVar2);
  return;
}


