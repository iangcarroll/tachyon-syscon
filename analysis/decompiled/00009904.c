/* UNREVIEWED Ghidra output: FUN_00009904 @ 00009904 */

uint FUN_00009904(undefined4 *param_1,byte *param_2,undefined4 *param_3,uint param_4)

{
  uint uVar1;
  undefined4 *puVar2;
  uint uVar3;
  byte *pbVar4;
  byte *pbVar5;
  uint uVar6;
  int iVar7;
  uint uVar8;
  uint uVar9;
  undefined8 uVar10;
  byte *local_2c;
  
  if ((param_4 == 1) || (pbVar5 = param_2, 0x24 < param_4)) {
    puVar2 = (undefined4 *)FUN_00009a54();
    *puVar2 = 0x16;
    return 0;
  }
  do {
    pbVar4 = pbVar5;
    uVar8 = (uint)*pbVar4;
    pbVar5 = pbVar4 + 1;
    uVar9 = *(byte *)(DAT_00009a18 + uVar8) & 8;
  } while ((*(byte *)(DAT_00009a18 + uVar8) & 8) != 0);
  if (uVar8 == 0x2d) {
    uVar9 = 1;
    uVar8 = (uint)*pbVar5;
    pbVar5 = pbVar4 + 2;
  }
  else if (uVar8 == 0x2b) {
    uVar8 = (uint)*pbVar5;
    pbVar5 = pbVar4 + 2;
  }
  if (param_4 == 0) {
    if (uVar8 != 0x30) {
      param_4 = 10;
      goto LAB_0000995a;
    }
  }
  else if ((param_4 != 0x10) || (uVar8 != 0x30)) goto LAB_0000995a;
  if ((*pbVar5 & 0xdf) == 0x58) {
    param_4 = 0x10;
    uVar8 = (uint)pbVar5[1];
    pbVar5 = pbVar5 + 2;
  }
  else {
    uVar8 = 0x30;
    if (param_4 == 0) {
      param_4 = 8;
    }
  }
LAB_0000995a:
  uVar6 = uVar9 + DAT_00009a1c;
  uVar10 = FUN_000001f4(uVar6,param_4);
  iVar7 = 0;
  uVar1 = 0;
  do {
    uVar3 = uVar8 - 0x30;
    if (9 < uVar3) {
      if (uVar8 - 0x41 < 0x1a) {
        uVar3 = uVar8 - 0x37;
      }
      else {
        if (0x19 < uVar8 - 0x61) break;
        uVar3 = uVar8 - 0x57;
      }
    }
    if ((int)param_4 <= (int)uVar3) break;
    if (iVar7 < 0) {
      iVar7 = -1;
    }
    else {
      iVar7 = -1;
      if ((uVar1 <= (uint)uVar10) &&
         (((uint)uVar10 != uVar1 || ((int)uVar3 <= (int)((ulonglong)uVar10 >> 0x20))))) {
        iVar7 = 1;
        uVar1 = uVar3 + param_4 * uVar1;
      }
    }
    uVar8 = (uint)*pbVar5;
    pbVar5 = pbVar5 + 1;
  } while( true );
  if (iVar7 < 0) {
    *param_1 = 0x22;
    uVar1 = uVar6;
    if (param_3 == (undefined4 *)0x0) {
      return uVar6;
    }
  }
  else {
    if (uVar9 != 0) {
      uVar1 = -uVar1;
    }
    if (param_3 == (undefined4 *)0x0) {
      return uVar1;
    }
    local_2c = param_2;
    if (iVar7 == 0) goto LAB_000099fc;
  }
  local_2c = pbVar5 + -1;
LAB_000099fc:
  *param_3 = local_2c;
  return uVar1;
}


