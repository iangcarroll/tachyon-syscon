/* UNREVIEWED Ghidra output: FUN_000050f4 @ 000050f4 */

undefined4 FUN_000050f4(void)

{
  undefined4 uVar1;
  int iVar2;
  undefined8 uVar3;
  
  iVar2 = FUN_00005004(0);
  uVar1 = DAT_00005134;
  if (iVar2 < 0) {
    FUN_00008f88(1,DAT_00005134,DAT_00005138);
  }
  uVar3 = FUN_000077b4();
  *DAT_0000513c = uVar3;
  *DAT_00005140 = 0;
  FUN_00008f88(3,uVar1,DAT_00005144,2000);
  return 1;
}


