/* UNREVIEWED Ghidra output: FUN_0000374c @ 0000374c */

undefined8 FUN_0000374c(undefined4 param_1,undefined4 param_2)

{
  int iVar1;
  int iVar2;
  int iVar3;
  undefined1 local_c;
  undefined1 local_b;
  undefined2 uStack_a;
  
  uStack_a = (undefined2)((uint)param_2 >> 0x10);
  iVar3 = 4;
  local_c = (undefined1)param_1;
  local_b = (undefined1)param_2;
  do {
    iVar1 = FUN_0000844c(0,0x26,&local_c,2);
    iVar2 = DAT_00003794;
    if (iVar1 == 2) goto LAB_00003790;
    iVar3 = iVar3 + -1;
  } while (iVar3 != 0);
  iVar3 = FUN_000098dc(DAT_00003794,0x2f);
  if (iVar3 != 0) {
    iVar2 = FUN_000098dc(iVar2,0x2f);
    iVar2 = iVar2 + 1;
  }
  FUN_00002678(iVar2,0x24,DAT_00003798);
LAB_00003790:
  return CONCAT26(uStack_a,CONCAT15(local_b,CONCAT14(local_c,param_1)));
}


