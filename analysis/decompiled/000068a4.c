/* UNREVIEWED Ghidra output: FUN_000068a4 @ 000068a4 */

int FUN_000068a4(void)

{
  int iVar1;
  undefined4 uVar2;
  
  uVar2 = DAT_000068f0;
  FUN_00008f88(3,DAT_000068f0,DAT_000068f4);
  FUN_00008054(0xb,1);
  iVar1 = FUN_00005f30();
  if (iVar1 != 0) {
    FUN_000066bc(4);
    uVar2 = 8;
  }
  else {
    FUN_00008f88(1,uVar2,DAT_000068f8);
    FUN_00006248();
    FUN_00007928(1);
    uVar2 = 0xb;
  }
  FUN_00008054(uVar2,iVar1 != 0);
  return iVar1;
}


