/* UNREVIEWED Ghidra output: FUN_00006948 @ 00006948 */

bool FUN_00006948(uint param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  char cVar1;
  undefined4 uVar2;
  undefined1 *puVar3;
  char *pcVar4;
  int iVar5;
  undefined4 uVar6;
  undefined8 uVar7;
  
  FUN_00006282();
  iVar5 = FUN_00004c50(0xf);
  pcVar4 = DAT_00006a08;
  puVar3 = DAT_00006a04;
  uVar2 = DAT_00006a00;
  if (DAT_000069fc < iVar5) {
    if (param_1 < 2) {
      FUN_00008f88(3,DAT_00006a00,DAT_00006a0c,DAT_000069fc,param_4);
      param_1 = 2;
    }
    *puVar3 = 2;
    *pcVar4 = '\x02';
    uVar7 = FUN_000077b4();
    *DAT_00006a10 = uVar7;
  }
  else {
    if (1 < param_1) {
      uVar6 = FUN_000066a0(param_1);
      FUN_00008f88(1,uVar2,DAT_00006a20,uVar6,param_4);
    }
    param_1 = 1;
    *puVar3 = 0;
    *pcVar4 = '\0';
  }
  FUN_000066bc(param_1);
  cVar1 = *pcVar4;
  uVar6 = DAT_00006a14;
  if (cVar1 != '\x02') {
    uVar6 = DAT_00006a18;
  }
  FUN_00008f88(3,uVar2,DAT_00006a1c,uVar6);
  if (cVar1 == '\x02') {
    FUN_0000614c();
    FUN_00007928(0);
  }
  else {
    FUN_00006248();
    FUN_00007928(1);
    iVar5 = FUN_00003150();
    if ((iVar5 != 0) && (iVar5 = FUN_00004fd0(), iVar5 < 0)) {
      FUN_00008f88(1,uVar2,DAT_00006a24);
    }
  }
  return cVar1 == '\x02';
}


