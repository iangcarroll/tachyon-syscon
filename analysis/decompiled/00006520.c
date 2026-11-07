/* UNREVIEWED Ghidra output: FUN_00006520 @ 00006520 */

undefined4 FUN_00006520(int param_1)

{
  undefined4 *puVar1;
  int iVar2;
  undefined1 uVar3;
  undefined4 uVar4;
  undefined1 auStack_70 [100];
  
  if (*DAT_000065a4 == '\0') {
    FUN_000055dc(0);
    *DAT_000065b0 = 0;
    *DAT_000065b4 = 0;
    FUN_00006282();
    FUN_00007928(0);
    puVar1 = DAT_000065c0;
    uVar4 = DAT_000065b8;
    if (param_1 == 0) {
      uVar4 = DAT_000065bc;
    }
    *DAT_000065c0 = uVar4;
    iVar2 = DAT_000065c8;
    uVar3 = 5;
    if (param_1 == 0) {
      uVar3 = 3;
    }
    *DAT_000065c4 = uVar3;
    FUN_00009748(auStack_70,iVar2 + 0x38,0x60);
    uVar3 = 0xc;
    if (param_1 == 0) {
      uVar3 = 5;
    }
    iVar2 = FUN_00007554(auStack_70,uVar3);
    uVar4 = 0;
    if (iVar2 < 0) {
      FUN_00008f88(3,DAT_000065ac,DAT_000065cc,*puVar1);
    }
  }
  else {
    FUN_00008f88(1,DAT_000065ac,DAT_000065a8);
    uVar4 = 0xffffffff;
  }
  return uVar4;
}


