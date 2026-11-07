/* UNREVIEWED Ghidra output: FUN_00005048 @ 00005048 */

longlong FUN_00005048(uint param_1,undefined4 param_2)

{
  uint uVar1;
  uint uVar2;
  undefined4 uVar3;
  int iVar4;
  int iVar5;
  
  uVar2 = param_1;
  uVar1 = FUN_00004d00();
  if (uVar1 == param_1) {
    FUN_00008f88(1,DAT_000050e0,DAT_000050e4,*(undefined4 *)(DAT_000050dc + uVar1 * 4),uVar2,param_2
                );
    goto LAB_00005064;
  }
  uVar2 = *(uint *)(DAT_000050dc + param_1 * 4);
  FUN_00008f88(3,DAT_000050e0,DAT_000050e8,*(undefined4 *)(DAT_000050dc + uVar1 * 4),uVar2,param_2);
  if ((param_1 == 0) || (param_1 == 1)) {
    FUN_0000364e(0x23,param_1);
    FUN_0000364e(0x1a,0);
    uVar3 = 0;
LAB_0000508e:
    FUN_00005004(uVar3);
  }
  else if (param_1 == 2) {
    FUN_0000364e(0x1a,1);
    FUN_0000364e(0x23,0);
    uVar3 = 1;
    goto LAB_0000508e;
  }
  uVar1 = FUN_00004d00();
  iVar5 = DAT_000050ec;
  if (param_1 != uVar1) {
    iVar4 = FUN_000098dc(DAT_000050ec,0x2f);
    if (iVar4 != 0) {
      iVar5 = FUN_000098dc(iVar5,0x2f);
      iVar5 = iVar5 + 1;
    }
    FUN_00002678(iVar5,0x168,DAT_000050f0);
  }
LAB_00005064:
  return (ulonglong)uVar2 << 0x20;
}


