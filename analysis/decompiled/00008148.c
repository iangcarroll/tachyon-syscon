/* UNREVIEWED Ghidra output: FUN_00008148 @ 00008148 */

longlong FUN_00008148(uint param_1,int param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int *piVar4;
  uint uVar5;
  uint uVar6;
  
  iVar3 = DAT_000081dc;
  if (0x18 < param_1) {
    iVar2 = FUN_000098dc(DAT_000081dc,0x2f);
    if (iVar2 != 0) {
      iVar3 = FUN_000098dc(iVar3,0x2f);
      iVar3 = iVar3 + 1;
    }
    FUN_00002678(iVar3,0x7a,DAT_000081e0);
  }
  piVar4 = (int *)FUN_00007a54(param_1 & 0xff);
  iVar3 = DAT_000081e4;
  uVar5 = (uint)*(byte *)(piVar4 + 1);
  *(undefined4 *)(param_1 * 8 + DAT_000081e4) = param_3;
  uVar6 = 1 << uVar5;
  *(undefined4 *)(iVar3 + param_1 * 8 + 4) = param_4;
  if ((param_2 != 1) && (param_2 != 2)) {
    param_2 = 3;
  }
  iVar3 = *piVar4;
  if (uVar5 < 0x10) {
    iVar2 = DAT_000081e8;
  }
  else {
    uVar5 = uVar5 - 0x10;
    iVar2 = 0x13a0;
  }
  *(uint *)(iVar3 + iVar2) = *(uint *)(iVar3 + iVar2) & ~(3 << (uVar5 << 1 & 0xff));
  iVar1 = DAT_000081ec;
  *(uint *)(iVar3 + iVar2) = param_2 << (uVar5 << 1 & 0xff) | *(uint *)(iVar3 + iVar2);
  *(uint *)(iVar3 + iVar1) = *(uint *)(iVar3 + iVar1) | uVar6;
  *(uint *)(iVar3 + DAT_000081f0) = uVar6 | *(uint *)(iVar3 + DAT_000081f0);
  *DAT_000081f4 = 2;
  return (ulonglong)param_1 << 0x20;
}


