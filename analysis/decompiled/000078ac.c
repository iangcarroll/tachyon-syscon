/* UNREVIEWED Ghidra output: FUN_000078ac @ 000078ac */

void FUN_000078ac(undefined4 param_1)

{
  undefined4 uVar1;
  int iVar2;
  undefined4 uVar3;
  
  iVar2 = FUN_00006690();
  uVar1 = DAT_000078f8;
  if (iVar2 == 0) {
    uVar3 = DAT_0000790c;
  }
  else {
    FUN_00008f88(3,DAT_000078f8,DAT_000078fc);
    FUN_000077fc(10);
    iVar2 = FUN_000080f8(param_1);
    if (iVar2 == 0) {
      FUN_00008f88(3,uVar1,DAT_00007900);
      *DAT_00007904 = 1;
      return;
    }
    uVar3 = DAT_00007908;
  }
  FUN_00008f88(3,uVar1,uVar3);
  return;
}


