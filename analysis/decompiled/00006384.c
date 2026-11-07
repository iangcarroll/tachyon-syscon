/* UNREVIEWED Ghidra output: FUN_00006384 @ 00006384 */

void FUN_00006384(uint param_1)

{
  char *pcVar1;
  undefined4 *puVar2;
  uint uVar3;
  undefined4 uVar4;
  undefined4 uVar5;
  undefined4 uVar6;
  undefined4 uVar7;
  bool bVar8;
  longlong lVar9;
  
  pcVar1 = DAT_00006404;
  bVar8 = false;
  if (*DAT_00006404 != '\0') {
    bVar8 = *DAT_00006408 == param_1;
  }
  *DAT_00006408 = (byte)param_1;
  puVar2 = DAT_0000640c;
  if ((param_1 - 3 < 4) || (param_1 == 0)) {
    if (!bVar8) {
      *DAT_0000640c = 0;
    }
    *pcVar1 = '\x01';
    uVar3 = FUN_000062ec(param_1,*puVar2);
    lVar9 = FUN_000077b4();
    *DAT_00006410 = lVar9 + (ulonglong)uVar3;
    uVar7 = *(undefined4 *)(param_1 * 4 + DAT_00006414);
    uVar6 = DAT_00006418;
    if (!bVar8) {
      uVar6 = DAT_0000641c;
    }
    uVar5 = *DAT_0000640c;
    uVar4 = FUN_000000e8(uVar3,1000);
    FUN_00008f88(3,DAT_00006424,DAT_00006420,uVar7,uVar6,uVar4,uVar5);
  }
  return;
}


