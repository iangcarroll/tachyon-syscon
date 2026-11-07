/* UNREVIEWED Ghidra output: FUN_00003488 @ 00003488 */

void FUN_00003488(void)

{
  uint *puVar1;
  uint *puVar2;
  char *pcVar3;
  undefined4 uVar4;
  byte bVar5;
  uint uVar6;
  undefined4 uVar7;
  undefined4 uVar8;
  undefined4 uVar9;
  undefined4 uVar10;
  undefined4 uVar11;
  undefined4 uVar12;
  int iVar13;
  int iVar14;
  undefined4 uVar15;
  int iVar16;
  undefined4 extraout_r1;
  uint uVar17;
  uint uVar18;
  uint uVar19;
  undefined8 uVar20;
  undefined1 *puVar21;
  undefined1 auStack_24 [16];
  
  puVar2 = DAT_000035dc;
  uVar6 = *DAT_000035dc;
  puVar1 = DAT_000035dc + 1;
  *DAT_000035dc = uVar6 + 1;
  puVar2[1] = *puVar1 + (uint)(0xfffffffe < uVar6);
  uVar20 = FUN_000077b4();
  puVar1 = DAT_000035e0;
  if (((uint)((ulonglong)uVar20 >> 0x20) != (uint)((uint)uVar20 < *DAT_000035e0)) ||
     (DAT_000035e4 < (uint)uVar20 - *DAT_000035e0)) {
    uVar6 = FUN_000077b4();
    uVar17 = *DAT_000035e8;
    *DAT_000035e8 = uVar6;
    uVar18 = *puVar2;
    uVar19 = puVar2[1];
    *puVar2 = 0;
    puVar2[1] = 0;
    pcVar3 = DAT_000035ec;
    *puVar1 = uVar6;
    if (*pcVar3 != '\0') {
      uVar20 = FUN_000077b4();
      uVar7 = FUN_00000448((int)uVar20,(int)((ulonglong)uVar20 >> 0x20),1000,0);
      uVar8 = FUN_00004c50(0xc);
      uVar9 = FUN_00004c50(0xd);
      uVar10 = FUN_00004c50(0xe);
      uVar11 = FUN_00004c50(0x10);
      uVar12 = FUN_00004c50(0xf);
      iVar13 = FUN_000080f8(0x11);
      iVar14 = FUN_00007d54();
      if (iVar14 == -0x80000000) {
        FUN_000092f4(auStack_24,0xc,DAT_000035f0);
      }
      else {
        iVar16 = FUN_000001fc(iVar14,10);
        FUN_000003c8(iVar14 + (iVar14 >> 0x1f) ^ iVar14 >> 0x1f,10);
        if ((iVar14 < 0) && (iVar16 == 0)) {
          FUN_000092f4(auStack_24,0xc,DAT_00003608);
        }
        else {
          FUN_000092f4(auStack_24,0xc,DAT_0000360c,iVar16,extraout_r1);
        }
      }
      bVar5 = FUN_00006690();
      uVar15 = FUN_000055c4();
      uVar4 = DAT_000035f4;
      FUN_00008f88(3,DAT_000035f4,DAT_000035f8,uVar8,uVar9,uVar10,uVar12,uVar11,uVar15);
      uVar8 = DAT_000035fc;
      if (iVar13 == 0) {
        uVar8 = DAT_00003600;
      }
      puVar21 = auStack_24;
      uVar11 = FUN_000000e8(uVar6 - uVar17,1000);
      uVar9 = FUN_00000448(uVar18,uVar19,uVar11,0,uVar9,uVar10,uVar8,puVar21);
      FUN_00008f88(3,uVar4,DAT_00003604,uVar7,bVar5 ^ 1,uVar9,uVar8,puVar21,uVar15);
    }
  }
  return;
}


