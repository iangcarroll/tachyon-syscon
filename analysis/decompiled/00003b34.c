/* UNREVIEWED Ghidra output: FUN_00003b34 @ 00003b34 */

/* WARNING: Function: __gnu_thumb1_case_uqi replaced with injection: switch8_r0 */
/* WARNING (jumptable): Removing unreachable block (ram,0x00003cf0) */
/* WARNING: Removing unreachable block (ram,0x00003cf0) */

void FUN_00003b34(void)

{
  char cVar1;
  char *pcVar2;
  int *piVar3;
  char *pcVar4;
  undefined4 uVar5;
  uint uVar6;
  int iVar7;
  undefined4 uVar8;
  undefined4 uVar9;
  int iVar10;
  int extraout_r1;
  undefined4 uVar11;
  byte bVar12;
  undefined4 uVar13;
  undefined1 auStack_24 [2];
  undefined2 local_22;
  undefined4 local_20;
  
  FUN_0000798c();
  uVar5 = FUN_00007b88();
  FUN_00007b78(1);
  FUN_00007be0();
  FUN_0000975a(auStack_24,0,9);
  local_20 = 0x1c200;
  local_22 = 9;
  FUN_00008954(0,auStack_24);
  FUN_00008fc0(1);
  FUN_000059d8();
  FUN_0000776c();
  FUN_00007540();
  FUN_000079d0();
  FUN_000030f0();
  FUN_00007910();
  FUN_00005b7c(0);
  uVar6 = FUN_00007c08();
  if ((uVar6 != 1) && (uVar6 != 6)) {
    FUN_00005afc();
  }
  FUN_00005970(0);
  FUN_00005908(DAT_00003e4c,0);
  FUN_000079d0();
  iVar7 = FUN_00003808(uVar6 < 2);
  uVar13 = DAT_00003e50;
  if (iVar7 < 0) {
    FUN_00008f88(1,DAT_00003e50,DAT_00003e54);
  }
  uVar11 = DAT_00003e58;
  FUN_00008f88(3,uVar13,DAT_00003e58);
  uVar8 = FUN_00007c3c(uVar6);
  uVar9 = FUN_00007bfc();
  uVar5 = FUN_00007b9c(uVar5);
  FUN_00008f88(3,uVar13,DAT_00003e5c,DAT_00003e60,uVar8,uVar9,uVar5);
  FUN_00008f88(3,uVar13,DAT_00003e68,DAT_00003e6c,DAT_00003e64);
  FUN_00005ac4();
  uVar5 = FUN_000066a0();
  iVar7 = FUN_00005af0();
  uVar9 = *(undefined4 *)(iVar7 * 4 + DAT_00003e70);
  uVar8 = FUN_00005b14();
  FUN_00008f88(3,uVar13,DAT_00003e74,uVar5,uVar9,uVar8);
  FUN_00008f88(3,uVar13,uVar11);
  iVar7 = FUN_000054cc(uVar6 < 2);
  if (iVar7 < 0) {
    FUN_00008f88(1,uVar13,DAT_00003e78,iVar7,uVar9,uVar8);
  }
  FUN_00005ac4();
  iVar7 = FUN_00006948();
  if (iVar7 < 0) {
    FUN_00008f88(1,DAT_00003e50,DAT_00003e7c);
  }
  FUN_00004c24();
  FUN_000079d0();
  if (uVar6 == 1) {
    iVar7 = FUN_00003114();
    iVar10 = FUN_00003144();
    if (iVar10 == 0) {
      if (iVar7 != 0) {
        FUN_00006428();
      }
    }
    else {
      FUN_00005c68(7,0);
    }
  }
  do {
    FUN_00007b78(2);
    FUN_00003488();
    FUN_00007b78(3);
    piVar3 = DAT_00003e84;
    pcVar2 = DAT_00003e80;
    if ((*DAT_00003e80 == '\0') && (iVar7 = FUN_00003b0c(DAT_00003e84), iVar7 != 0)) {
      iVar7 = FUN_00003b0c(piVar3);
      if (iVar7 == 0) {
        FUN_00008f88(1,DAT_00003e50,DAT_00003e88,0xffffffff);
        bVar12 = 0xff;
      }
      else {
        bVar12 = *(byte *)(*piVar3 + piVar3[3]);
        FUN_000001f4(piVar3[3] + 1,piVar3[1]);
        piVar3[3] = extraout_r1;
        *(undefined1 *)(piVar3 + 4) = 0;
      }
      iVar7 = FUN_00003144();
      pcVar4 = DAT_00003e8c;
      uVar5 = DAT_00003e50;
      if (iVar7 == 0) {
        if (bVar12 < 6) {
          cVar1 = *DAT_00003e8c;
          switch(bVar12) {
          case 0:
            FUN_00008f88(3,DAT_00003e50,DAT_00003e90,cVar1);
            iVar7 = FUN_00006690();
            uVar13 = DAT_00003e94;
            *pcVar4 = (char)iVar7;
            if (iVar7 == 0) {
              uVar13 = DAT_00003e98;
            }
            iVar7 = FUN_00003138();
            uVar11 = DAT_00003e9c;
            if (iVar7 == 0) {
              uVar11 = DAT_00003ea0;
            }
            FUN_00008f88(3,uVar5,DAT_00003ea4,uVar13,uVar11);
            if ((*pcVar4 != '\0') && (iVar7 = FUN_00003138(), iVar7 != 0)) {
LAB_00003d5a:
              FUN_00005e24();
            }
            break;
          case 1:
            FUN_00008f88(3,DAT_00003e50,DAT_00003ea8,cVar1);
            if (*pcVar4 != '\0') {
              FUN_00006428();
            }
            break;
          case 2:
            FUN_00008f88(3,DAT_00003e50,DAT_00003eac,cVar1);
            iVar7 = FUN_00003138();
            if (iVar7 != 0) goto LAB_00003d5a;
            if (*pcVar4 == '\0') {
LAB_00003dfe:
              FUN_00003ad4();
            }
            else {
LAB_00003dd6:
              FUN_000064a0();
            }
            break;
          case 3:
            FUN_00008f88(3,DAT_00003e50,DAT_00003eb0,cVar1);
            if (*pcVar4 == '\0') {
              iVar7 = FUN_00003138();
              if (iVar7 != 0) goto LAB_00003dfe;
            }
            else {
              iVar7 = FUN_00003138();
              if (iVar7 != 0) goto LAB_00003dd6;
            }
            break;
          case 4:
            FUN_00008f88(3,DAT_00003e50,DAT_00003eb4,cVar1);
            iVar7 = FUN_00003138();
            if ((iVar7 != 0) && (*pcVar4 != '\0')) goto LAB_00003d5a;
            break;
          case 5:
            FUN_00008f88(3,DAT_00003e50,DAT_00003eb8,cVar1);
            if ((*pcVar4 != '\0') && (iVar7 = FUN_00003138(), iVar7 != 0)) {
              FUN_000065e4();
            }
          }
        }
        else {
          FUN_00008f88(1,DAT_00003e50,DAT_00003ebc,bVar12);
        }
      }
    }
    FUN_00007b78(4);
    FUN_00004c14();
    FUN_00007b78(5);
    FUN_00006a68();
    FUN_000079d0();
    FUN_00007b78(6);
    FUN_000075d8();
    FUN_00007b78(7);
    if ((*pcVar2 != '\0') && (iVar7 = FUN_000076d8(), iVar7 == 0)) {
      *pcVar2 = '\0';
      FUN_00006720(1);
    }
    FUN_00007b78(8);
    FUN_00007974();
  } while( true );
}


