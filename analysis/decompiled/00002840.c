/* UNREVIEWED Ghidra output: FUN_00002840 @ 00002840 */

int FUN_00002840(int param_1)

{
  int iVar1;
  uint uVar2;
  byte local_1a;
  byte local_19 [5];
  
  iVar1 = FUN_000027dc();
  if (iVar1 != 0) {
    iVar1 = FUN_000027dc(param_1 + 0x20);
    if (iVar1 != 0) {
      local_1a = 0;
      local_19[0] = 0;
      FUN_00009748(&local_1a,param_1 + 0x1f,1);
      FUN_00009748(local_19,(undefined1 *)(param_1 + 0x3f),1);
      uVar2 = FUN_0000282c(param_1);
      if (local_1a == uVar2) {
        uVar2 = FUN_0000282c(param_1 + 0x20);
        if (local_19[0] == uVar2) {
          return iVar1;
        }
        FUN_00008f88(1,DAT_000028cc,DAT_000028d0,uVar2,*(undefined1 *)(param_1 + 0x3f));
      }
      else {
        FUN_00008f88(1,DAT_000028cc,DAT_000028c8);
      }
    }
  }
  return 0;
}


