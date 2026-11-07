/* UNREVIEWED Ghidra output: FUN_00004fd0 @ 00004fd0 */

undefined4 FUN_00004fd0(void)

{
  int iVar1;
  undefined4 uVar2;
  
  iVar1 = FUN_00004d9c();
  if (iVar1 == 1) {
    FUN_00008f88(3,DAT_00004ff8,DAT_00004ffc);
    uVar2 = 0;
  }
  else {
    FUN_00008f88(3,DAT_00004ff8,DAT_00005000);
    uVar2 = FUN_00004ee0(2);
  }
  return uVar2;
}


