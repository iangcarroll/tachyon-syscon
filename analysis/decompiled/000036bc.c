/* UNREVIEWED Ghidra output: FUN_000036bc @ 000036bc */

undefined8 FUN_000036bc(undefined4 param_1,undefined4 param_2)

{
  int iVar1;
  int iVar2;
  int iVar3;
  undefined4 uStack_14;
  
  iVar3 = 4;
  uStack_14 = CONCAT13((char)param_1,(int3)param_2);
  do {
    iVar1 = FUN_0000844c(0,0x26,(int)&uStack_14 + 3,1);
    iVar2 = DAT_00003740;
    if (iVar1 == 1) goto LAB_00003702;
    iVar3 = iVar3 + -1;
  } while (iVar3 != 0);
  iVar3 = FUN_000098dc(DAT_00003740,0x2f);
  if (iVar3 != 0) {
    iVar2 = FUN_000098dc(iVar2,0x2f);
    iVar2 = iVar2 + 1;
  }
  FUN_00002678(iVar2,0x29,DAT_00003744);
LAB_00003702:
  iVar3 = 4;
  do {
    iVar1 = FUN_0000860c(0,0x26,param_2,1);
    iVar2 = DAT_00003740;
    if (iVar1 == 1) goto LAB_0000373e;
    iVar3 = iVar3 + -1;
  } while (iVar3 != 0);
  iVar3 = FUN_000098dc(DAT_00003740,0x2f);
  if (iVar3 != 0) {
    iVar2 = FUN_000098dc(iVar2,0x2f);
    iVar2 = iVar2 + 1;
  }
  FUN_00002678(iVar2,0x2a,DAT_00003748);
LAB_0000373e:
  return CONCAT44(uStack_14,param_1);
}


