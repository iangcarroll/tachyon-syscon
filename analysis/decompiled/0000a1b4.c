/* UNREVIEWED Ghidra output: FUN_0000a1b4 @ 0000a1b4 */

/* WARNING: Function: __gnu_thumb1_case_shi replaced with injection: switch16_shi_r0 */
/* WARNING (jumptable): Removing unreachable block (ram,0x0000a1ee) */
/* WARNING: Removing unreachable block (ram,0x0000a1ee) */

uint FUN_0000a1b4(undefined4 param_1,uint *param_2,undefined4 param_3,code *param_4,int *param_5)

{
  bool bVar1;
  byte bVar2;
  int iVar3;
  int iVar4;
  uint *puVar5;
  uint uVar6;
  undefined1 *puVar7;
  undefined4 *puVar8;
  uint uVar9;
  uint uVar10;
  undefined1 *puVar11;
  undefined8 uVar12;
  int local_34;
  uint local_1c [2];
  
  puVar7 = (undefined1 *)((int)param_2 + 0x43);
  bVar2 = (byte)param_2[6];
  if (0x78 < bVar2) {
switchD_0000a1ee_caseD_65:
    *(byte *)((int)param_2 + 0x42) = bVar2;
LAB_0000a22c:
    puVar11 = (undefined1 *)((int)param_2 + 0x42);
    uVar10 = 1;
LAB_0000a380:
    param_2[4] = uVar10;
    *puVar7 = 0;
    goto LAB_0000a2dc;
  }
  puVar11 = puVar7;
  if (bVar2 < 99) {
    if (bVar2 == 0) goto LAB_0000a35c;
    if (bVar2 == 0x58) {
      *(undefined1 *)((int)param_2 + 0x45) = 0x58;
      local_34 = DAT_0000a3d0;
      goto LAB_0000a2fe;
    }
    goto switchD_0000a1ee_caseD_65;
  }
  switch(bVar2) {
  case 99:
    puVar8 = (undefined4 *)*param_5;
    *param_5 = (int)(puVar8 + 1);
    *(char *)((int)param_2 + 0x42) = (char)*puVar8;
    goto LAB_0000a22c;
  case 100:
  case 0x69:
    uVar6 = *param_2;
    puVar5 = (uint *)*param_5;
    if ((int)(uVar6 << 0x18) < 0) {
      uVar10 = *puVar5;
      *param_5 = (int)(puVar5 + 1);
    }
    else {
      uVar10 = *puVar5;
      *param_5 = (int)(puVar5 + 1);
      if ((int)(uVar6 << 0x19) < 0) {
        uVar10 = (uint)(short)uVar10;
      }
    }
    if ((int)uVar10 < 0) {
      uVar10 = -uVar10;
      *puVar7 = 0x2d;
    }
    uVar6 = 10;
    local_34 = DAT_0000a3d0;
    goto LAB_0000a28a;
  default:
    goto switchD_0000a1ee_caseD_65;
  case 0x6e:
    puVar8 = (undefined4 *)*param_5;
    uVar6 = *param_2;
    uVar10 = param_2[5];
    *param_5 = (int)(puVar8 + 1);
    puVar5 = (uint *)*puVar8;
    if (((int)(uVar6 << 0x18) < 0) || (-1 < (int)(uVar6 << 0x19))) {
      *puVar5 = uVar10;
    }
    else {
      *(short *)puVar5 = (short)uVar10;
    }
LAB_0000a35c:
    param_2[4] = 0;
    goto LAB_0000a2dc;
  case 0x6f:
  case 0x75:
    uVar10 = *param_2;
    puVar5 = (uint *)*param_5;
    *param_5 = (int)(puVar5 + 1);
    if (((int)(uVar10 << 0x18) < 0) || (-1 < (int)(uVar10 << 0x19))) {
      uVar10 = *puVar5;
    }
    else {
      uVar10 = *puVar5 & 0xffff;
    }
    uVar6 = 8;
    local_34 = DAT_0000a3d0;
    if (bVar2 != 0x6f) {
      uVar6 = 10;
    }
    break;
  case 0x70:
    *param_2 = *param_2 | 0x20;
  case 0x78:
    *(undefined1 *)((int)param_2 + 0x45) = 0x78;
    local_34 = DAT_0000a3d4;
LAB_0000a2fe:
    uVar6 = *param_2;
    uVar10 = *(uint *)*param_5;
    *param_5 = (int)((uint *)*param_5 + 1);
    if ((-1 < (int)(uVar6 << 0x18)) && ((int)(uVar6 << 0x19) < 0)) {
      uVar10 = uVar10 & 0xffff;
    }
    if ((int)(uVar6 << 0x1f) < 0) {
      *param_2 = uVar6 | 0x20;
    }
    uVar6 = 0x10;
    if (uVar10 == 0) {
      *param_2 = *param_2 & 0xffffffdf;
    }
    break;
  case 0x73:
    puVar8 = (undefined4 *)*param_5;
    *param_5 = (int)(puVar8 + 1);
    puVar11 = (undefined1 *)*puVar8;
    iVar3 = FUN_0000a8b0(puVar11,0,param_2[1]);
    if (iVar3 != 0) {
      param_2[1] = iVar3 - (int)puVar11;
    }
    uVar10 = param_2[1];
    goto LAB_0000a380;
  }
  *(undefined1 *)((int)param_2 + 0x43) = 0;
LAB_0000a28a:
  uVar9 = param_2[1];
  param_2[2] = uVar9;
  if (-1 < (int)uVar9) {
    *param_2 = *param_2 & 0xfffffffb;
  }
  if ((uVar10 != 0) || (uVar9 != 0)) {
    do {
      uVar12 = FUN_000001f4(uVar10,uVar6);
      puVar11 = puVar11 + -1;
      *puVar11 = *(undefined1 *)(local_34 + (int)((ulonglong)uVar12 >> 0x20));
      bVar1 = uVar6 <= uVar10;
      uVar10 = (uint)uVar12;
    } while (bVar1);
  }
  if (((uVar6 == 8) && ((int)(*param_2 << 0x1f) < 0)) && ((int)param_2[1] <= (int)param_2[4])) {
    puVar11 = puVar11 + -1;
    *puVar11 = 0x30;
  }
  param_2[4] = (int)puVar7 - (int)puVar11;
LAB_0000a2dc:
  iVar3 = FUN_0000a0d4(param_1,param_2,local_1c,param_3,param_4);
  if ((iVar3 == -1) || (iVar3 = (*param_4)(param_1,param_3,puVar11,param_2[4]), iVar3 == -1)) {
LAB_0000a2f0:
    uVar10 = 0xffffffff;
  }
  else {
    if ((int)(*param_2 << 0x1e) < 0) {
      for (iVar3 = 0; iVar3 < (int)(param_2[3] - local_1c[0]); iVar3 = iVar3 + 1) {
        iVar4 = (*param_4)(param_1,param_3,(int)param_2 + 0x19,1);
        if (iVar4 == -1) goto LAB_0000a2f0;
      }
    }
    uVar10 = param_2[3];
    if ((int)param_2[3] < (int)local_1c[0]) {
      uVar10 = local_1c[0];
    }
  }
  return uVar10;
}


