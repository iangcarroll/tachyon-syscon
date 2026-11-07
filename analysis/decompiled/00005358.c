/* UNREVIEWED Ghidra output: FUN_00005358 @ 00005358 */

void FUN_00005358(code *param_1)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  int iVar7;
  int iVar8;
  int iVar9;
  
  iVar1 = FUN_00004c50(0xc);
  uVar2 = FUN_00004c50(0xd);
  uVar3 = FUN_00004c50(0xe);
  iVar4 = FUN_00004c50(0x10);
  iVar5 = FUN_00004c50(0xf);
  iVar6 = FUN_00004ca8();
  iVar7 = FUN_00005af0();
  iVar8 = FUN_00004d00();
  iVar9 = FUN_00004d9c();
  (*param_1)(DAT_00005450);
  (*param_1)(DAT_00005458,*(undefined4 *)(iVar7 * 4 + DAT_00005454),uVar3);
  iVar7 = FUN_00004d58();
  uVar3 = DAT_0000545c;
  if (iVar7 != 1) {
    uVar3 = DAT_00005460;
  }
  (*param_1)(DAT_00005464,uVar3);
  iVar7 = FUN_00004df4();
  (*param_1)(DAT_0000546c,*(undefined4 *)(iVar7 * 4 + DAT_00005468));
  uVar3 = DAT_00005474;
  if (iVar4 <= DAT_00005470) {
    uVar3 = DAT_00005478;
  }
  (*param_1)(DAT_0000547c,uVar3,iVar4);
  iVar4 = FUN_00003620(0x20);
  uVar3 = DAT_00005480;
  if (iVar4 == 0) {
    uVar3 = DAT_00005484;
  }
  (*param_1)(DAT_00005488,uVar3);
  (*param_1)(DAT_00005490,*(undefined4 *)(iVar9 * 4 + DAT_0000548c),uVar2);
  iVar4 = FUN_00004ec4();
  uVar3 = DAT_00005494;
  if (iVar4 == 0) {
    uVar3 = DAT_00005498;
  }
  (*param_1)(DAT_0000549c,uVar3);
  (*param_1)(DAT_000054a4,*(undefined4 *)(iVar8 * 4 + DAT_000054a0));
  (*param_1)(DAT_000054ac,*(undefined4 *)(iVar6 * 4 + DAT_000054a8));
  uVar3 = DAT_000054b4;
  if (iVar5 <= DAT_000054b0) {
    uVar3 = DAT_000054b8;
  }
  (*param_1)(DAT_000054bc,uVar3,iVar5);
  uVar3 = DAT_000054b4;
  if (iVar1 <= DAT_000054c0) {
    uVar3 = DAT_000054b8;
  }
  (*param_1)(DAT_000054c4,uVar3,iVar1);
  (*param_1)(DAT_000054c8);
  return;
}


