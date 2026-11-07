/* UNREVIEWED Ghidra output: FUN_00005b7c @ 00005b7c */

undefined4 FUN_00005b7c(undefined1 param_1)

{
  undefined4 uVar1;
  int iVar2;
  
  FUN_000087dc(3);
  FUN_000087dc(2);
  FUN_000087dc(1);
  iVar2 = DAT_00005bc4;
  FUN_0000975a(DAT_00005bc4,0,0x14);
  uVar1 = DAT_00005bc8;
  *(undefined1 *)(iVar2 + 0x10) = param_1;
  iVar2 = FUN_0000781c(0x14,0,uVar1);
  if (iVar2 < 0) {
    FUN_00008f88(1,DAT_00005bd0,DAT_00005bcc);
  }
  FUN_0000776c();
  return 0;
}


