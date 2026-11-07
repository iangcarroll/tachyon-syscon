/* UNREVIEWED Ghidra output: FUN_00004e34 @ 00004e34 */

longlong FUN_00004e34(uint param_1,undefined4 param_2,undefined4 param_3)

{
  int iVar1;
  undefined4 uVar2;
  uint uVar3;
  undefined4 uVar4;
  uint uVar5;
  
  uVar5 = param_1;
  uVar3 = FUN_00004ca8();
  uVar2 = DAT_00004eb8;
  iVar1 = DAT_00004eb4;
  if (uVar3 == param_1) {
    FUN_00008f88(3,DAT_00004eb8,DAT_00004ebc,*(undefined4 *)(DAT_00004eb4 + uVar3 * 4),uVar5,param_2
                 ,param_3);
    goto LAB_00004e52;
  }
  if (uVar3 != 0) {
    FUN_0000364e(0x21,0);
    FUN_0000364e(0x22,0);
  }
  if (param_1 == 1) {
    FUN_00004e04(0);
    FUN_00004d68(0);
    uVar4 = 0x21;
LAB_00004e7e:
    FUN_0000364e(uVar4,1);
  }
  else {
    if (param_1 == 2) {
      FUN_00004e04(1);
      FUN_00004d68(1);
      uVar4 = 0x22;
      goto LAB_00004e7e;
    }
    FUN_00004e04(1);
  }
  uVar5 = *(uint *)(iVar1 + param_1 * 4);
  FUN_00008f88(3,uVar2,DAT_00004ec0,*(undefined4 *)(iVar1 + uVar3 * 4),uVar5,param_2,param_3);
LAB_00004e52:
  return (ulonglong)uVar5 << 0x20;
}


