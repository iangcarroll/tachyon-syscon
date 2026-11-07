/* UNREVIEWED Ghidra output: FUN_00009ddc @ 00009ddc */

/* WARNING: Function: __gnu_thumb1_case_shi replaced with injection: switch16_shi_r0 */
/* WARNING (jumptable): Removing unreachable block (ram,0x00009ede) */
/* WARNING: Removing unreachable block (ram,0x00009ede) */

int FUN_00009ddc(int param_1,undefined4 *param_2,byte *param_3,undefined4 param_4)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  int iVar7;
  int iVar8;
  int iVar9;
  int iVar10;
  int iVar11;
  int iVar12;
  int iVar13;
  int iVar14;
  int iVar15;
  int iVar16;
  int iVar17;
  int iVar18;
  int iVar19;
  int iVar20;
  int iVar21;
  int iVar22;
  uint uVar23;
  byte *pbVar24;
  code *pcVar25;
  undefined4 uVar26;
  undefined4 *puVar27;
  uint uVar28;
  byte *pbVar29;
  undefined1 uStack000000f8;
  undefined1 uStack000000fc;
  undefined1 uStack00000100;
  undefined1 uStack00000104;
  undefined1 uStack00000108;
  undefined1 uStack0000010c;
  undefined1 uStack00000110;
  undefined4 auStack_7ffffffc [536870906];
  
  iVar20 = DAT_0000a0bc;
  iVar1 = DAT_0000a0bc + 0x7fffffe8;
  iVar2 = DAT_0000a0bc + 0x7fffffe8;
  iVar3 = DAT_0000a0bc + 0x7fffffe8;
  iVar4 = DAT_0000a0bc + 0x7fffffe8;
  iVar5 = DAT_0000a0bc + 0x7fffffe8;
  iVar6 = DAT_0000a0bc + 0x7fffffe8;
  iVar7 = DAT_0000a0bc + 0x7fffffe8;
  iVar8 = DAT_0000a0bc + 0x7fffffe8;
  iVar9 = DAT_0000a0bc + 0x7fffffe8;
  iVar10 = DAT_0000a0bc + 0x7fffffe8;
  iVar11 = DAT_0000a0bc + 0x7fffffe8;
  iVar12 = DAT_0000a0bc + 0x7fffffe8;
  iVar13 = DAT_0000a0bc + 0x7fffffe8;
  iVar14 = DAT_0000a0bc + 0x7fffffe8;
  iVar15 = DAT_0000a0bc + 0x7fffffe8;
  iVar16 = DAT_0000a0bc + 0x7fffffe8;
  iVar17 = DAT_0000a0bc + 0x7fffffe8;
  iVar18 = DAT_0000a0bc + 0x7fffffe8;
  iVar19 = DAT_0000a0bc + 0x7fffffe8;
  *(undefined4 *)(&uStack00000104 + DAT_0000a0bc) = 0;
  *(undefined4 *)(&uStack00000108 + DAT_0000a0bc) = 0;
  *(int *)(&uStack0000010c + DAT_0000a0bc) = (int)auStack_7ffffffc + DAT_0000a0bc + 0x7ffffff4;
  *(undefined4 *)((int)register0x00000054 + DAT_0000a0bc + 0x274) = DAT_0000a0c0;
  *(undefined4 *)((int)register0x00000054 + DAT_0000a0bc + 0x278) = DAT_0000a0c4;
  *(undefined4 *)((int)auStack_7ffffffc + DAT_0000a0bc + 0x7ffffff0) = param_4;
LAB_00009e06:
  do {
    iVar22 = DAT_0000a0cc;
    uVar28 = (uint)*param_3;
    if (uVar28 == 0) goto LAB_0000a0b8;
    pbVar29 = param_3 + 1;
    uVar23 = *(byte *)(DAT_0000a0c8 + uVar28) & 8;
    if ((*(byte *)(DAT_0000a0c8 + uVar28) & 8) != 0) {
      do {
        param_3 = pbVar29;
        if ((int)param_2[1] < 1) {
          pcVar25 = *(code **)((int)register0x00000054 + iVar20 + 0x278);
          *(code **)((int)auStack_7ffffffc + iVar2) = pcVar25;
          iVar22 = (*pcVar25)(param_1,param_2);
          if (iVar22 != 0) goto LAB_00009e06;
        }
        pbVar24 = (byte *)*param_2;
        if ((*(byte *)(DAT_0000a0c8 + (uint)*pbVar24) & 8) == 0) goto LAB_00009e06;
        iVar22 = *(int *)(&uStack00000108 + iVar20);
        *(int *)((int)auStack_7ffffffc + iVar1) = iVar22;
        *(int *)(&uStack00000108 + iVar20) = iVar22 + 1;
        *param_2 = pbVar24 + 1;
        param_2[1] = param_2[1] + -1;
      } while( true );
    }
    if (uVar28 == 0x25) {
      *(uint *)(&uStack00000100 + iVar20) = uVar23;
      *(uint *)(&uStack000000f8 + iVar20) = uVar23;
      if (param_3[1] == 0x2a) {
        *(undefined4 *)(&uStack000000f8 + iVar20) = 0x10;
        pbVar29 = param_3 + 2;
      }
      while( true ) {
        uVar28 = (uint)*pbVar29;
        *(byte **)((int)auStack_7ffffffc + iVar3) = pbVar29 + 1;
        if (9 < uVar28 - 0x30) break;
        iVar21 = *(int *)(&uStack00000100 + iVar20);
        pbVar29 = *(byte **)((int)auStack_7ffffffc + iVar5);
        *(int *)((int)auStack_7ffffffc + iVar20 + 0x7fffffec) = iVar21;
        *(uint *)(&uStack00000100 + iVar20) = iVar21 * 10 + -0x30 + uVar28;
      }
      iVar21 = FUN_0000a8b0(DAT_0000a0cc,uVar28,3);
      if (iVar21 != 0) {
        uVar28 = *(uint *)(&uStack000000f8 + iVar20);
        pbVar29 = *(byte **)((int)auStack_7ffffffc + iVar4);
        *(uint *)((int)auStack_7ffffffc + iVar20 + 0x7fffffec) = uVar28;
        *(uint *)(&uStack000000f8 + iVar20) = 1 << (iVar21 - iVar22 & 0xffU) | uVar28;
      }
      param_3 = pbVar29 + 1;
      uVar28 = (uint)*pbVar29;
      if (0x78 < uVar28) {
switchD_00009ede_caseD_59:
        *(undefined4 *)(&uStack00000110 + iVar20) = 3;
        *(undefined4 *)(&uStack000000fc + iVar20) = 10;
        goto LAB_00009fa2;
      }
      if (uVar28 < 0x58) {
        pbVar29 = param_3;
        if (uVar28 == 0x25) goto LAB_00009f2e;
        if (uVar28 < 0x26) {
          if (uVar28 == 0) {
            return -1;
          }
        }
        else if (uVar28 - 0x45 < 3) goto switchD_00009ede_caseD_65;
        goto switchD_00009ede_caseD_59;
      }
      switch(uVar28) {
      default:
        goto switchD_00009ede_caseD_59;
      case 0x5b:
        param_3 = (byte *)FUN_0000a69c((int)auStack_7ffffffc + iVar20 + 0x7ffffff4,param_3);
        *(undefined4 *)((int)auStack_7ffffffc + iVar13) = *(undefined4 *)(&uStack000000f8 + iVar20);
        *(uint *)(&uStack000000f8 + iVar20) = *(uint *)((int)auStack_7ffffffc + iVar14) | 0x40;
        uVar26 = 1;
        break;
      case 99:
        *(undefined4 *)((int)auStack_7ffffffc + iVar15) = *(undefined4 *)(&uStack000000f8 + iVar20);
        *(uint *)(&uStack000000f8 + iVar20) = *(uint *)((int)auStack_7ffffffc + iVar16) | 0x40;
        uVar26 = 0;
        break;
      case 100:
      case 0x75:
        uVar26 = 10;
LAB_00009f94:
        *(undefined4 *)(&uStack000000fc + iVar20) = uVar26;
        iVar22 = (0x6e < uVar28) + 3;
        goto LAB_00009fa0;
      case 0x65:
      case 0x66:
      case 0x67:
switchD_00009ede_caseD_65:
        uVar26 = 5;
        break;
      case 0x69:
        iVar22 = 3;
        *(undefined4 *)(&uStack000000fc + iVar20) = 0;
        goto LAB_00009fa0;
      case 0x6e:
        iVar22 = *(int *)(&uStack000000f8 + iVar20);
        if (-1 < iVar22 << 0x1b) {
          puVar27 = *(undefined4 **)((int)auStack_7ffffffc + iVar20 + 0x7ffffff0);
          uVar26 = *(undefined4 *)(&uStack00000108 + iVar20);
          *(undefined4 **)((int)auStack_7ffffffc + iVar20 + 0x7ffffff0) = puVar27 + 1;
          puVar27 = (undefined4 *)*puVar27;
          if (iVar22 << 0x1f < 0) {
            *(short *)puVar27 = (short)uVar26;
          }
          else {
            *puVar27 = uVar26;
          }
        }
        goto LAB_00009e06;
      case 0x6f:
        iVar22 = 4;
        *(undefined4 *)(&uStack000000fc + iVar20) = 8;
LAB_00009fa0:
        *(int *)(&uStack00000110 + iVar20) = iVar22;
        goto LAB_00009fa2;
      case 0x70:
        *(undefined4 *)((int)auStack_7ffffffc + iVar8) = *(undefined4 *)(&uStack000000f8 + iVar20);
        *(uint *)(&uStack000000f8 + iVar20) = *(uint *)((int)auStack_7ffffffc + iVar9) | 0x20;
      case 0x58:
      case 0x78:
        *(undefined4 *)((int)auStack_7ffffffc + iVar10) = *(undefined4 *)(&uStack000000f8 + iVar20);
        *(uint *)(&uStack000000f8 + iVar20) = *(uint *)((int)auStack_7ffffffc + iVar11) | 0x200;
        uVar26 = 0x10;
        goto LAB_00009f94;
      case 0x73:
        uVar26 = 2;
      }
      *(undefined4 *)(&uStack00000110 + iVar20) = uVar26;
LAB_00009fa2:
      if ((int)param_2[1] < 1) {
        pcVar25 = *(code **)((int)register0x00000054 + iVar20 + 0x278);
        *(code **)((int)auStack_7ffffffc + iVar17) = pcVar25;
        iVar22 = (*pcVar25)(param_1,param_2);
        if (iVar22 != 0) goto LAB_00009f66;
      }
      iVar22 = *(int *)(&uStack000000f8 + iVar20);
      *(int *)((int)auStack_7ffffffc + iVar12) = iVar22;
      if (-1 < iVar22 << 0x19) {
        while (pbVar29 = (byte *)*param_2, (*(byte *)(DAT_0000a0c8 + (uint)*pbVar29) & 8) != 0) {
          iVar22 = *(int *)(&uStack00000108 + iVar20);
          *(int *)((int)auStack_7ffffffc + iVar18) = iVar22;
          *(int *)(&uStack00000108 + iVar20) = iVar22 + 1;
          iVar22 = param_2[1];
          param_2[1] = iVar22 + -1;
          if (iVar22 + -1 < 1) {
            pcVar25 = *(code **)((int)register0x00000054 + iVar20 + 0x278);
            *(code **)((int)auStack_7ffffffc + iVar19) = pcVar25;
            iVar22 = (*pcVar25)(param_1,param_2);
            if (iVar22 != 0) goto LAB_00009f66;
          }
          else {
            *param_2 = pbVar29 + 1;
          }
        }
      }
      if (*(int *)(&uStack00000110 + iVar20) < 3) {
        iVar22 = FUN_0000a3d8(param_1,&uStack000000f8 + iVar20,param_2,
                              (int)auStack_7ffffffc + iVar20 + 0x7ffffff0);
      }
      else if (*(int *)(&uStack00000110 + iVar20) < 5) {
        iVar22 = FUN_0000a494(param_1,&uStack000000f8 + iVar20,param_2,
                              (int)auStack_7ffffffc + iVar20 + 0x7ffffff0);
      }
      else {
        iVar22 = param_1;
        if (DAT_0000a0d0 == 0) goto LAB_00009e06;
      }
      if (iVar22 == 1) {
LAB_0000a0b8:
        return *(int *)(&uStack00000104 + iVar20);
      }
      if (iVar22 == 2) {
LAB_00009f66:
        if (*(int *)(&uStack00000104 + iVar20) == 0) {
          return -1;
        }
        if ((int)((uint)*(ushort *)(param_2 + 3) << 0x19) < 0) {
          return -1;
        }
        return *(int *)(&uStack00000104 + iVar20);
      }
      goto LAB_00009e06;
    }
LAB_00009f2e:
    if ((int)param_2[1] < 1) {
      pcVar25 = *(code **)((int)register0x00000054 + iVar20 + 0x278);
      *(code **)((int)auStack_7ffffffc + iVar7) = pcVar25;
      iVar22 = (*pcVar25)(param_1,param_2);
      if (iVar22 != 0) goto LAB_00009f66;
    }
    if (*(byte *)*param_2 != uVar28) goto LAB_0000a0b8;
    iVar22 = param_2[1];
    *param_2 = (byte *)*param_2 + 1;
    iVar21 = *(int *)(&uStack00000108 + iVar20);
    *(int *)((int)auStack_7ffffffc + iVar6) = iVar21;
    param_2[1] = iVar22 + -1;
    *(int *)(&uStack00000108 + iVar20) = iVar21 + 1;
    param_3 = pbVar29;
  } while( true );
}


