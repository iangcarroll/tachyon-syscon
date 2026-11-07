/* UNREVIEWED Ghidra output: FUN_00009038 @ 00009038 */

/* WARNING: Function: __gnu_thumb1_case_uqi replaced with injection: switch8_r0 */
/* WARNING: Function: __gnu_thumb1_case_sqi replaced with injection: switchS8_r0 */
/* WARNING (jumptable): Removing unreachable block (ram,0x000090de) */
/* WARNING (jumptable): Removing unreachable block (ram,0x0000910c) */
/* WARNING (jumptable): Removing unreachable block (ram,0x000091ea) */
/* WARNING (jumptable): Removing unreachable block (ram,0x0000918c) */
/* WARNING: Removing unreachable block (ram,0x000091ea) */
/* WARNING: Removing unreachable block (ram,0x0000910c) */
/* WARNING: Removing unreachable block (ram,0x000090de) */
/* WARNING: Removing unreachable block (ram,0x0000918c) */

undefined4 FUN_00009038(undefined4 param_1,undefined4 param_2,byte *param_3,uint *param_4)

{
  byte bVar1;
  byte bVar2;
  int iVar3;
  undefined4 uVar4;
  uint uVar5;
  uint *puVar6;
  char cVar7;
  byte *pbVar8;
  byte *pbVar9;
  byte bVar10;
  undefined1 *puVar11;
  uint uVar12;
  int iVar13;
  bool bVar14;
  byte *local_48;
  int local_44;
  undefined4 local_3c;
  undefined4 local_38;
  undefined4 local_34;
  undefined1 local_30 [28];
  
  local_34 = 0;
  local_3c = param_1;
  local_38 = param_2;
  do {
    bVar1 = *param_3;
    if (bVar1 == 0) {
      return local_34;
    }
    if (bVar1 != 0x25) goto switchD_0000910c_caseD_65;
    local_44 = 0;
    pbVar8 = param_3;
    bVar10 = 0;
    while( true ) {
      bVar2 = pbVar8[1];
      if (bVar2 == 0) break;
      if (bVar2 == 0x23) {
        local_44 = 0x23;
LAB_00009064:
        bVar2 = bVar10;
      }
      else if (bVar2 != 0x2b) {
        if (bVar2 != 0x20) break;
        if (bVar10 != 0) goto LAB_00009064;
      }
      pbVar8 = pbVar8 + 1;
      bVar10 = bVar2;
    }
    pbVar9 = pbVar8 + 2;
    if (bVar2 == 0x6c) {
      uVar4 = 4;
      if (pbVar8[2] == 0x6c) {
        pbVar9 = pbVar8 + 3;
        uVar4 = 5;
      }
    }
    else if (bVar2 < 0x6d) {
      if (bVar2 == 0x68) {
        uVar4 = 1;
        if (pbVar8[2] == 0x68) {
          pbVar9 = pbVar8 + 3;
          uVar4 = 3;
        }
      }
      else {
        uVar4 = 6;
        if (bVar2 != 0x6a) goto LAB_000090a0;
      }
    }
    else {
      uVar4 = 8;
      if ((bVar2 != 0x74) && (uVar4 = 7, bVar2 != 0x7a)) {
LAB_000090a0:
        uVar4 = 0;
        pbVar9 = pbVar8 + 1;
      }
    }
    local_48 = pbVar9 + 1;
    bVar2 = *pbVar9;
    if (0x78 < bVar2) goto switchD_0000910c_caseD_65;
    if (bVar2 < 99) {
      if (bVar2 == 0x25) {
        cVar7 = '\x01';
        goto LAB_0000912e;
      }
      iVar13 = 0;
      cVar7 = '\x06';
      if (bVar2 == 0x58) goto LAB_000090d0;
      goto switchD_0000910c_caseD_65;
    }
    switch(bVar2) {
    case 99:
      cVar7 = '\x02';
      goto LAB_0000912e;
    case 100:
    case 0x69:
      iVar13 = 0x20;
      cVar7 = '\x04';
      break;
    default:
      goto switchD_0000910c_caseD_65;
    case 0x6f:
      iVar13 = 0x20;
      cVar7 = '\x05';
      break;
    case 0x70:
      cVar7 = '\b';
      goto LAB_0000912e;
    case 0x73:
      cVar7 = '\x03';
LAB_0000912e:
      iVar13 = 0x20;
      break;
    case 0x75:
      iVar13 = 0x20;
      cVar7 = '\a';
      break;
    case 0x78:
      iVar13 = 0x20;
      cVar7 = '\x06';
    }
LAB_000090d0:
    if (param_3 == local_48) {
switchD_0000910c_caseD_65:
      local_48 = param_3 + 1;
      FUN_00009028(bVar1,&local_3c);
      goto LAB_0000905e;
    }
                    /* WARNING: Could not find normalized switch variable to match jumptable */
    switch(cVar7) {
    case '\x02':
      local_30[0] = (undefined1)*param_4;
      param_4 = param_4 + 1;
      goto LAB_00009156;
    case '\x03':
      puVar11 = (undefined1 *)*param_4;
      param_4 = param_4 + 1;
      for (iVar3 = 0; puVar11[iVar3] != '\0'; iVar3 = iVar3 + 1) {
      }
LAB_00009284:
      for (iVar13 = 0; iVar13 < iVar3; iVar13 = iVar13 + 1) {
        FUN_00009028(puVar11[iVar13],&local_3c);
      }
      goto LAB_0000905e;
    case '\x04':
      switch(uVar4) {
      case 1:
        uVar5 = (uint)(short)*param_4;
        break;
      default:
        uVar5 = *param_4;
        break;
      case 3:
        uVar12 = 0;
        uVar5 = *param_4;
        param_4 = param_4 + 1;
        uVar5 = uVar5 & 0xff;
        goto LAB_000091a6;
      case 5:
      case 6:
        puVar6 = (uint *)((int)param_4 + 7U & 0xfffffff8);
        param_4 = puVar6 + 2;
        uVar5 = *puVar6;
        uVar12 = puVar6[1];
        goto LAB_000091d8;
      }
      param_4 = param_4 + 1;
      uVar12 = (int)uVar5 >> 0x1f;
LAB_000091d8:
      if ((int)uVar12 < 0) {
        bVar10 = 0x2d;
      }
LAB_000091a6:
      if ((int)uVar12 < 0) {
        bVar14 = uVar5 != 0;
        uVar5 = -uVar5;
        uVar12 = -(uint)bVar14 - uVar12;
      }
      iVar3 = FUN_00008fcc(uVar5,uVar12,local_30,10,iVar13);
      if (bVar10 != 0) {
        FUN_00009028(bVar10,&local_3c);
      }
      break;
    case '\x05':
    case '\x06':
    case '\a':
      switch(uVar4) {
      case 1:
        uVar12 = *param_4 & 0xffff;
        break;
      default:
        uVar12 = *param_4;
        break;
      case 3:
        uVar12 = *param_4 & 0xff;
        break;
      case 5:
      case 6:
        param_4 = (uint *)((int)param_4 + 7U & 0xfffffff8);
        uVar12 = *param_4;
        uVar5 = param_4[1];
        param_4 = param_4 + 2;
        goto LAB_00009212;
      }
      param_4 = param_4 + 1;
      uVar5 = 0;
LAB_00009212:
      uVar4 = 8;
      if ((cVar7 != '\x05') && (uVar4 = 0x10, cVar7 != '\x06')) {
        uVar4 = 10;
      }
      iVar3 = FUN_00008fcc(uVar12,uVar5,local_30,uVar4,iVar13);
      if ((uVar12 == 0 && uVar5 == 0) || (local_44 == 0)) {
LAB_0000927a:
        puVar11 = local_30;
        if (cVar7 == '\x03') goto LAB_00009284;
      }
      else {
        if (cVar7 != '\x05') {
          if (cVar7 == '\x06') {
            FUN_00009028(0x30,&local_3c);
            FUN_00009028(iVar13 + 0x58,&local_3c);
          }
          goto LAB_0000927a;
        }
        local_30[iVar3] = 0x30;
        iVar3 = iVar3 + 1;
      }
      break;
    default:
      local_30[0] = 0x25;
LAB_00009156:
      iVar3 = 1;
    }
    for (; 0 < iVar3; iVar3 = iVar3 + -1) {
      FUN_00009028(local_30[iVar3 + -1],&local_3c);
    }
LAB_0000905e:
    param_3 = local_48;
  } while( true );
}


