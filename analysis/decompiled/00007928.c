/* UNREVIEWED Ghidra output: FUN_00007928 @ 00007928 */

void FUN_00007928(int param_1)

{
  undefined4 uVar1;
  int iVar2;
  
  uVar1 = DAT_00007964;
  if ((param_1 == 0) || (iVar2 = FUN_00003120(), iVar2 == 0)) {
    FUN_00008f88(3,uVar1,DAT_00007970);
    FUN_000081f8(0x11);
  }
  else {
    FUN_00008f88(3,uVar1,DAT_00007968);
    FUN_00008148(0x11,2,DAT_0000796c,0);
  }
  return;
}


