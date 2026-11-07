/* UNREVIEWED Ghidra output: FUN_00006838 @ 00006838 */

int FUN_00006838(void)

{
  int iVar1;
  undefined4 uVar2;
  
  uVar2 = DAT_00006890;
  FUN_00008f88(3,DAT_00006890,DAT_00006894,*DAT_0000688c);
  iVar1 = FUN_00005f30();
  if (iVar1 == 0) {
    FUN_00008f88(1,uVar2,DAT_00006898);
    FUN_00006248();
    FUN_00007928(1);
  }
  else {
    FUN_000066bc(*DAT_0000689c);
    FUN_0000364e(0x1d,0);
    FUN_00008054(8,1);
    uVar2 = FUN_000077b4();
    *DAT_000068a0 = uVar2;
  }
  return iVar1;
}


