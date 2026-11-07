/* UNREVIEWED Ghidra output: FUN_00003668 @ 00003668 */

undefined8 FUN_00003668(undefined4 param_1,undefined4 param_2,undefined4 param_3)

{
  int iVar1;
  int iVar2;
  int iVar3;
  undefined1 local_14;
  undefined1 local_13;
  undefined1 local_12;
  undefined1 uStack_11;
  undefined4 uStack_10;
  
  uStack_11 = (undefined1)((uint)param_2 >> 0x18);
  iVar3 = 4;
  local_13 = (undefined1)param_2;
  local_14 = (undefined1)param_1;
  local_12 = (undefined1)((uint)param_2 >> 8);
  uStack_10 = param_3;
  do {
    iVar1 = FUN_0000844c(0,0x26,&local_14,3);
    iVar2 = DAT_000036b4;
    if (iVar1 == 3) goto LAB_000036b0;
    iVar3 = iVar3 + -1;
  } while (iVar3 != 0);
  iVar3 = FUN_000098dc(DAT_000036b4,0x2f);
  if (iVar3 != 0) {
    iVar2 = FUN_000098dc(iVar2,0x2f);
    iVar2 = iVar2 + 1;
  }
  FUN_00002678(iVar2,0x34,DAT_000036b8);
LAB_000036b0:
  return CONCAT17(uStack_11,CONCAT16(local_12,CONCAT15(local_13,CONCAT14(local_14,param_1))));
}


