/* UNREVIEWED Ghidra output: FUN_00006a68 @ 00006a68 */

void FUN_00006a68(void)

{
  byte *pbVar1;
  byte bVar2;
  char cVar3;
  char cVar4;
  uint *puVar5;
  uint *puVar6;
  char *pcVar7;
  char *pcVar8;
  byte *pbVar9;
  undefined1 *puVar10;
  int *piVar11;
  int iVar12;
  int iVar13;
  uint uVar14;
  undefined4 uVar15;
  int iVar16;
  int iVar17;
  undefined4 uVar18;
  int iVar19;
  int iVar20;
  undefined4 *puVar21;
  undefined4 extraout_r1;
  byte *pbVar22;
  undefined4 uVar23;
  undefined4 uVar24;
  uint uVar25;
  bool bVar26;
  uint uVar27;
  uint uVar28;
  char cVar29;
  undefined8 uVar30;
  longlong lVar31;
  byte local_2c [2];
  bool local_2a;
  undefined4 local_28;
  undefined4 uStack_24;
  undefined4 uStack_20;
  undefined4 local_1c;
  
  FUN_00005694();
  iVar12 = FUN_00004c50(0xf);
  iVar13 = DAT_00006be4;
  if (DAT_00006be4 < iVar12) {
    FUN_0000559c();
  }
  puVar5 = DAT_00006be8;
  if (*DAT_00006be8 != 0 || DAT_00006be8[1] != 0) {
    uVar30 = FUN_000077b4();
    uVar14 = (uint)((ulonglong)uVar30 >> 0x20);
    if ((puVar5[1] <= uVar14) && ((puVar5[1] != uVar14 || (*puVar5 <= (uint)uVar30)))) {
      *puVar5 = 0;
      puVar5[1] = 0;
      *DAT_00006bec = '\0';
      FUN_00008f88(3,DAT_00006bf0,DAT_00006bf4);
      FUN_00004e34(1);
      FUN_000055b4();
    }
  }
  pcVar8 = DAT_00006f90;
  pcVar7 = DAT_00006c00;
  puVar6 = DAT_00006bfc;
  if (iVar13 < iVar12) {
    if (*DAT_00006bf8 == '\0') {
      if (*DAT_00006c00 == '\x01') {
        *DAT_00006bf8 = '\x02';
        *pcVar7 = '\x02';
        *puVar6 = 0;
        puVar6[1] = 0;
        FUN_0000614c();
        uVar18 = FUN_00004c50(0xc);
        iVar13 = FUN_00004ca8();
        uVar24 = DAT_00006bf0;
        uVar15 = *(undefined4 *)(iVar13 * 4 + DAT_00006c04);
        FUN_00008f88(3,DAT_00006bf0,DAT_00006c08,uVar18,uVar15);
        if (*DAT_00006bec != '\0') {
          lVar31 = FUN_000077b4();
          *(longlong *)puVar5 = lVar31 + 0x32;
        }
        FUN_000055b4();
        uVar30 = FUN_000077b4();
        puVar5 = DAT_00006c10;
        *DAT_00006c0c = uVar30;
        if ((*puVar5 | puVar5[1]) != 0) {
          FUN_00008f88(3,uVar24,DAT_00006c14,*puVar5 | puVar5[1],uVar15);
          *puVar5 = 0;
          puVar5[1] = 0;
        }
        if (*DAT_00006c18 == '\0') {
          uVar15 = DAT_00006fc4;
LAB_00006e56:
          FUN_00008f88(3,uVar24,uVar15);
        }
        else {
          *DAT_00006c18 = '\0';
          iVar13 = FUN_0000562c();
          iVar12 = FUN_00005670();
          if (iVar13 == 1) {
            uVar18 = DAT_00006c1c;
            if (iVar12 == 0) {
              uVar18 = DAT_00006c20;
            }
            FUN_00008f88(3,uVar24,DAT_00006c24,uVar18);
          }
          else {
            uVar15 = DAT_00006c1c;
            if (iVar12 == 0) {
              uVar15 = DAT_00006c20;
            }
            FUN_00008f88(2,uVar24,DAT_00006c44,*(undefined4 *)(iVar13 * 4 + DAT_00006c40),uVar15);
          }
          FUN_000055dc(0);
          pcVar7 = DAT_00006c2c;
          *DAT_00006c28 = 0;
          *DAT_00006c30 = 0;
          if (*pcVar7 == '\x05') {
            iVar13 = FUN_000077b4();
            uVar14 = iVar13 - *DAT_00006c34;
            if (iVar13 != *DAT_00006c34) {
              if (DAT_00006f7c < uVar14) {
                FUN_00008f88(1,uVar24,DAT_00006fb8,uVar14,uVar15);
                FUN_00006720(1);
                local_28 = *(uint *)(DAT_00006fbc + 0x18);
                uStack_24 = *(undefined4 *)(DAT_00006fbc + 0x1c);
                uStack_20 = *(undefined4 *)(DAT_00006fbc + 0x20);
                local_1c = *(undefined4 *)(DAT_00006fbc + 0x24);
                iVar13 = FUN_00007554(&local_28,2);
                uVar15 = DAT_00006fc0;
                if (iVar13 < 0) goto LAB_00006e56;
              }
              else {
                FUN_00008f88(3,uVar24,DAT_00006f80,uVar14,uVar15);
              }
              goto LAB_00006c5a;
            }
            FUN_00008f88(3,uVar24,DAT_00006c38,uVar14,uVar15);
          }
          cVar3 = *pcVar7;
          if (cVar3 != '\x02') {
            FUN_00008f88(3,uVar24,DAT_00006c3c,cVar3,uVar15);
            goto LAB_00006bc0;
          }
        }
      }
      else if (*DAT_00006c00 == '\0') {
        FUN_00008f88(1,DAT_00006f8c,DAT_00006fd0);
        *DAT_00006f88 = '\x02';
        *pcVar7 = '\x02';
        *puVar6 = 0;
        puVar6[1] = 0;
        FUN_0000614c();
        FUN_00007928(0);
LAB_00006bc0:
        FUN_000066bc(2);
      }
    }
  }
  else if (*DAT_00006bf8 == '\x02') {
    if (*DAT_00006f90 == '\x03') {
      *DAT_00006f90 = '\0';
      pcVar7 = DAT_00006f88;
      *puVar6 = 0;
      puVar6[1] = 0;
      *pcVar7 = '\0';
      FUN_00005e30();
      uVar15 = DAT_00006fcc;
      puVar21 = DAT_00006fc8;
      *DAT_00006fc8 = 0;
      puVar21[1] = 0;
      uVar24 = DAT_00006f8c;
      goto LAB_00006e56;
    }
    if (*DAT_00006f90 == '\x02') {
      FUN_0000559c();
      uVar14 = FUN_000055c4();
      uVar24 = FUN_00004c50(0xe);
      iVar13 = FUN_0000562c();
      if ((iVar13 == 0) && (uVar14 <= DAT_00006fd4)) {
        FUN_000055dc(6);
      }
      iVar13 = FUN_0000562c();
      iVar12 = FUN_00005670();
      uVar15 = DAT_00006fdc;
      if (iVar12 == 0) {
        uVar15 = DAT_00006fe0;
      }
      FUN_00008f88(2,DAT_00006f8c,DAT_00006fe4,*(undefined4 *)(iVar13 * 4 + DAT_00006fd8),uVar15,
                   uVar14,uVar24);
      FUN_000055b4();
      uVar24 = FUN_0000567c();
      pcVar7 = DAT_00006f84;
      *pcVar8 = '\x01';
      *pcVar7 = '\x01';
      puVar21 = DAT_00006fc8;
      *DAT_00006fc8 = 0;
      puVar21[1] = 0;
      *DAT_00006f88 = '\0';
      lVar31 = FUN_000077b4();
      *(longlong *)puVar6 = lVar31 + 0xfa;
      FUN_00006384(uVar24);
    }
  }
LAB_00006c5a:
  if (*puVar6 != 0 || puVar6[1] != 0) {
    uVar30 = FUN_000077b4();
    pcVar7 = DAT_00006f90;
    uVar24 = DAT_00006f8c;
    uVar14 = (uint)((ulonglong)uVar30 >> 0x20);
    if ((puVar6[1] < uVar14) || ((puVar6[1] == uVar14 && (*puVar6 < (uint)uVar30)))) {
      if (*DAT_00006f84 == '\0') {
        if ((*DAT_00006f88 != '\0') || (*DAT_00006f90 != '\x01')) goto LAB_00007020;
        FUN_00008f88(1,DAT_00006f8c,DAT_00007308);
        bVar2 = *DAT_0000730c;
        FUN_00006720(1);
        if (2 < bVar2 - 3) {
          FUN_0000567c();
          FUN_00006384();
        }
      }
      else if ((*DAT_00006f88 == '\0') && (*DAT_00006f90 == '\x01')) {
        *DAT_00006f84 = '\0';
        iVar13 = FUN_0000567c();
        if (iVar13 == 1) {
          FUN_00008f88(3,uVar24,DAT_00006f94);
          FUN_00006428();
        }
        else {
          if (((iVar13 - 3U & 0xff) < 4) || (iVar13 == 0)) {
            FUN_00008f88(3,uVar24,DAT_00006fec,*(undefined4 *)(iVar13 * 4 + DAT_00006fd8));
          }
          else {
            FUN_00008f88(3,uVar24,DAT_00006fe8);
          }
          FUN_00006720(1);
        }
      }
      else {
LAB_00007020:
        FUN_00008f88(1,DAT_00006f8c,DAT_00007310);
      }
      *pcVar7 = *DAT_00006f88;
      *puVar6 = 0;
      puVar6[1] = 0;
    }
  }
  iVar13 = FUN_000080f8(0x12);
  local_2c[0] = iVar13 == 1;
  iVar13 = FUN_000080f8(0x13);
  local_2c[1] = iVar13 == 1;
  iVar13 = FUN_000080f8(0x14);
  pbVar9 = DAT_00006f98;
  iVar12 = 0;
  local_2a = iVar13 == 1;
  pbVar22 = DAT_00006f98;
  do {
    pbVar1 = local_2c + iVar12;
    iVar12 = iVar12 + 1;
    *pbVar22 = *pbVar22 << 1 | *pbVar1;
    pbVar22 = pbVar22 + 1;
  } while (iVar12 != 3);
  FUN_0000975a(&local_28,0,3);
  puVar10 = DAT_00006f9c;
  FUN_00009748(&local_28,DAT_00006f9c,3);
  iVar13 = 0;
  puVar21 = &local_28;
  do {
    if (pbVar9[iVar13] == 0) {
      *(undefined1 *)puVar21 = 0;
    }
    else if ((pbVar9[iVar13] & 7) == 7) {
      *(undefined1 *)puVar21 = 1;
    }
    iVar13 = iVar13 + 1;
    puVar21 = (undefined4 *)((int)puVar21 + 1);
  } while (iVar13 != 3);
  iVar13 = FUN_0000972c(puVar10,&local_28);
  uVar24 = DAT_00006f8c;
  if (iVar13 != 0) {
    uVar15 = DAT_00006fa0;
    if ((char)local_28 == '\0') {
      uVar15 = DAT_00006fa4;
    }
    uVar18 = DAT_00006fa0;
    if (local_28._1_1_ == '\0') {
      uVar18 = DAT_00006fa4;
    }
    uVar23 = DAT_00006fa0;
    if (local_28._2_1_ == '\0') {
      uVar23 = DAT_00006fa4;
    }
    FUN_00008f88(3,DAT_00006f8c,DAT_00006fa8,uVar15,uVar18,uVar23);
    uVar14 = FUN_000077b4();
    *DAT_00006fac = uVar14;
    if (local_28._1_1_ == '\0') {
LAB_00006d8e:
      if ((((char)local_28 == '\0') && (local_28._1_1_ == '\0')) && (local_28._2_1_ == '\0')) {
        uVar30 = FUN_000077b4();
        if (((uint)((ulonglong)uVar30 >> 0x20) == (uint)((uint)uVar30 < *DAT_00007314)) &&
           ((uint)uVar30 - *DAT_00007314 < 0x96)) {
          FUN_00008f88(3,uVar24,DAT_00007318,0,uVar18,uVar23);
          FUN_00008f88(3,uVar24,DAT_0000731c);
        }
      }
    }
    else if (((char)local_28 == '\0') && (local_28._2_1_ == '\0')) {
      uVar15 = FUN_000077b4();
      *DAT_00006fb0 = uVar15;
      goto LAB_00006d8e;
    }
    *puVar10 = (char)local_28;
    puVar10[1] = local_28._1_1_;
    puVar10[2] = local_28._2_1_;
  }
  uVar25 = local_28 >> 8 & 0xff;
  uVar14 = 0;
  uVar28 = 0;
  if (uVar25 != 0) {
    uVar27 = local_28 >> 0x10 & 0xff;
    if ((local_28 & 0xff) == 0) {
      uVar14 = 0;
      uVar28 = 0;
      if (uVar27 != 0) {
        uVar25 = 0;
        uVar14 = 0;
        uVar28 = uVar27;
      }
    }
    else {
      uVar14 = uVar27 ^ 1;
      uVar25 = 0;
      uVar28 = 0;
    }
  }
  bVar26 = false;
  if (*DAT_00006fac != 0) {
    uVar30 = FUN_000077b4();
    bVar26 = true;
    if (((uint)((ulonglong)uVar30 >> 0x20) == (uint)((uint)uVar30 < *DAT_00006fac)) &&
       ((uint)uVar30 - *DAT_00006fac < 0x3e9)) {
      bVar26 = false;
    }
  }
  iVar13 = FUN_00005dbc();
  if (bVar26) {
    if (uVar25 == 0) {
      if (uVar28 != 0) {
        iVar12 = 6;
        goto LAB_00007084;
      }
      iVar12 = 7;
      if (uVar14 != 0) goto LAB_00007084;
LAB_00006e1c:
      FUN_00008f88(3,DAT_00006f8c,DAT_00006fb4);
    }
    else {
      iVar12 = 5;
LAB_00007084:
      if (iVar13 == iVar12) goto LAB_00006e1c;
      FUN_00008f88(3,DAT_00006f8c,DAT_00007320,iVar13,iVar12);
      FUN_00005c68(iVar12,0);
    }
    *DAT_00007324 = 0;
  }
  FUN_000049d0(DAT_00007328);
  iVar12 = FUN_00004c50(0x10);
  pcVar7 = DAT_00007330;
  iVar13 = DAT_0000732c;
  bVar26 = DAT_0000732c < iVar12;
  if (*DAT_00007330 == '\0') {
    *DAT_00007334 = bVar26;
    *pcVar7 = '\x01';
  }
  cVar3 = *DAT_00007338;
  cVar4 = *DAT_0000733c;
  iVar16 = FUN_00003114();
  puVar5 = DAT_00007340;
  if (*DAT_00007340 == 0 && DAT_00007340[1] == 0) {
    if (!(cVar3 != '\0' || cVar4 != '\0')) goto LAB_000071da;
LAB_000072b2:
    if (*DAT_00007360 != '\0') {
LAB_00007264:
      puVar5 = DAT_00007378;
      if ((*DAT_00007378 != 0 || DAT_00007378[1] != 0) && (*DAT_00007338 == '\x02')) {
        uVar30 = FUN_000077b4();
        piVar11 = DAT_0000736c;
        uVar14 = *puVar5;
        if (((int)((ulonglong)uVar30 >> 0x20) - puVar5[1] != (uint)((uint)uVar30 < uVar14)) ||
           (DAT_0000737c < (uint)uVar30 - uVar14)) {
          FUN_00008f88(3,DAT_00007354,DAT_00007380,0x78,*DAT_0000736c);
          pcVar7 = DAT_00007360;
          *piVar11 = 0;
          *pcVar7 = '\0';
          *DAT_00007368 = 0;
        }
      }
    }
  }
  else {
    if (!(cVar3 == '\0' && cVar4 == '\0')) goto LAB_000072b2;
    uVar30 = FUN_000077b4();
    uVar14 = (uint)((ulonglong)uVar30 >> 0x20);
    uVar25 = puVar5[1];
    if ((uVar14 < uVar25) || ((uVar25 == uVar14 && ((uint)uVar30 < *puVar5)))) goto LAB_000071da;
    iVar19 = FUN_00007d54();
    iVar20 = FUN_00004c50(0xd);
    iVar17 = FUN_0000562c();
    uVar30 = FUN_00005638();
    if (iVar19 < 500) {
      if (iVar17 != 3) {
        if (((iVar17 - 3U & 0xff) < 4) || (iVar17 == 0)) goto LAB_000071b4;
LAB_000071c2:
        FUN_00008f88(3,DAT_00007354,DAT_0000735c);
        puVar5 = DAT_00007340;
        *DAT_00007340 = 0;
        puVar5[1] = 0;
        FUN_00006428();
        goto LAB_000071da;
      }
      if (iVar13 < iVar12 || iVar13 < iVar20) {
LAB_000071b4:
        if (((int)((ulonglong)uVar30 >> 0x20) != 0) ||
           (*(uint *)(iVar17 * 4 + DAT_00007358) <= (uint)uVar30)) goto LAB_000071c2;
      }
    }
    uVar30 = FUN_000077b4();
    puVar5 = DAT_00007344;
    uVar14 = (uint)((ulonglong)uVar30 >> 0x20);
    if ((DAT_00007344[1] <= uVar14) &&
       ((DAT_00007344[1] != uVar14 || (*DAT_00007344 <= (uint)uVar30)))) {
      lVar31 = FUN_000077b4();
      iVar20 = DAT_0000734c;
      *(ulonglong *)puVar5 = lVar31 + (ulonglong)DAT_00007348;
      uVar23 = *(undefined4 *)(iVar17 * 4 + iVar20);
      uVar30 = FUN_00005638();
      FUN_000003c8(iVar19,10);
      uVar24 = extraout_r1;
      uVar15 = FUN_000001fc(iVar19,10);
      uVar18 = FUN_00000448((int)uVar30,(int)((ulonglong)uVar30 >> 0x20),1000,0);
      FUN_00008f88(2,DAT_00007354,DAT_00007350,uVar23,uVar18,uVar15,uVar24);
    }
LAB_000071da:
    if (iVar16 == 0) goto LAB_000072b2;
    if (*DAT_00007360 != '\0') {
      iVar19 = FUN_0000517c();
      if (iVar19 != 0) goto LAB_000072b2;
      uVar30 = FUN_000077b4();
      pbVar9 = DAT_00007368;
      uVar14 = (uint)((ulonglong)uVar30 >> 0x20);
      if (((uVar14 < DAT_00007364[1]) ||
          ((DAT_00007364[1] == uVar14 && ((uint)uVar30 < *DAT_00007364)))) ||
         ((*DAT_00007368 == 3 &&
          ((iVar19 = FUN_00004c50(0xd), iVar12 <= iVar13 && (iVar19 <= iVar13))))))
      goto LAB_000072b2;
      piVar11 = DAT_0000736c;
      bVar2 = *pbVar9;
      *DAT_0000736c = *DAT_0000736c + 1;
      uVar14 = FUN_000062ec((uint)bVar2);
      lVar31 = FUN_000077b4();
      *(ulonglong *)DAT_00007364 = lVar31 + (ulonglong)uVar14;
      uVar24 = FUN_000000e8(uVar14,1000);
      FUN_00008f88(3,DAT_00007354,DAT_00007370,*piVar11,
                   *(undefined4 *)((uint)bVar2 * 4 + DAT_0000734c),uVar24);
      FUN_00006428();
      pcVar7 = DAT_00007360;
      *pbVar9 = bVar2;
      *pcVar7 = '\x01';
      *DAT_00007374 = '\0';
      goto LAB_00007264;
    }
  }
  iVar19 = FUN_0000567c();
  cVar29 = *DAT_00007360;
  if ((cVar29 == '\0') || (*DAT_00007368 == 0)) {
    cVar29 = iVar19 == 2;
  }
  iVar20 = FUN_0000517c();
  pcVar8 = DAT_00007374;
  pcVar7 = DAT_00007334;
  if (((iVar20 == 0) && (cVar3 == '\0' && cVar4 == '\0')) && (iVar16 != 0)) {
    if (cVar29 == '\0') {
      if ((*DAT_00007334 == '\0') && (iVar13 < iVar12)) {
        uVar30 = FUN_000077b4();
        uVar24 = DAT_00007454;
        *(undefined8 *)DAT_00007450 = uVar30;
        *pcVar8 = '\x01';
        FUN_00008f88(3,DAT_0000744c,uVar24,DAT_00007458);
        goto LAB_000072ea;
      }
      if (*DAT_00007374 == '\0') {
        if (iVar13 < iVar12) goto LAB_000072ea;
      }
      else {
        if (iVar13 < iVar12) {
          uVar30 = FUN_000077b4();
          if (((int)((ulonglong)uVar30 >> 0x20) - DAT_00007450[1] !=
               (uint)((uint)uVar30 < *DAT_00007450)) ||
             (DAT_0000745c < (uint)uVar30 - *DAT_00007450)) {
            FUN_00008f88(3,DAT_0000744c,DAT_00007460);
            *pcVar8 = '\0';
            FUN_00006428();
          }
          goto LAB_000072ea;
        }
        FUN_00008f88(3,DAT_0000744c,DAT_00007464);
      }
    }
    else if ((*DAT_00007334 == '\0') && (iVar13 < iVar12)) {
      if (*DAT_0000743c == '\0') {
        uVar24 = *(undefined4 *)(DAT_00007440 + iVar19 * 4);
      }
      else {
        uVar24 = *(undefined4 *)(DAT_00007440 + (uint)*DAT_00007444 * 4);
      }
      FUN_00008f88(3,DAT_0000744c,DAT_00007448,uVar24);
    }
  }
  *pcVar8 = '\0';
LAB_000072ea:
  *pcVar7 = bVar26;
  return;
}


