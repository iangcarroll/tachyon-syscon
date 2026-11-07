/* UNREVIEWED Ghidra output: FUN_00005694 @ 00005694 */

void FUN_00005694(void)

{
  byte bVar1;
  byte *pbVar2;
  char *pcVar3;
  uint uVar4;
  uint uVar5;
  undefined8 uVar6;
  
  pbVar2 = DAT_000056f0;
  bVar1 = *DAT_000056f0;
  uVar4 = *DAT_000056f4;
  uVar5 = DAT_000056f4[1];
  uVar6 = FUN_000077b4();
  pcVar3 = DAT_000056f8;
  if ((((*DAT_000056f8 == '\0') && (bVar1 != 0)) && (uVar4 != 0 || uVar5 != 0)) &&
     (((int)((ulonglong)uVar6 >> 0x20) - uVar5 != (uint)((uint)uVar6 < uVar4) ||
      (DAT_000056fc < (uint)uVar6 - uVar4)))) {
    FUN_00008f88(2,DAT_00005708,DAT_00005704,*(undefined4 *)((uint)*pbVar2 * 4 + DAT_00005700),5);
    *pcVar3 = '\x01';
  }
  return;
}


