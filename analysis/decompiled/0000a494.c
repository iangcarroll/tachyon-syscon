/* UNREVIEWED Ghidra output: FUN_0000a494 @ 0000a494 */

undefined4 FUN_0000a494(undefined4 param_1,uint *param_2,int *param_3,undefined4 *param_4)

{
  int iVar1;
  undefined4 uVar2;
  uint *puVar3;
  uint uVar4;
  byte *pbVar5;
  undefined4 *puVar6;
  int iVar7;
  uint *local_3c;
  int local_38;
  code *local_30;
  undefined4 local_24 [4];
  
  local_24[0] = *DAT_0000a684;
  local_24[1] = DAT_0000a684[1];
  local_24[2] = DAT_0000a684[2];
  local_30 = DAT_0000a688;
  if (param_2[6] != 3) {
    local_30 = DAT_0000a68c;
  }
  local_38 = 0;
  if (0x15c < param_2[2] - 1) {
    local_38 = param_2[2] - 0x15d;
    param_2[2] = 0x15d;
  }
  puVar3 = param_2 + 7;
  iVar7 = 0;
  *param_2 = *param_2 | 0xd00;
  local_3c = puVar3;
  do {
    iVar1 = FUN_0000a8b0(local_24[iVar7],*(undefined1 *)*param_3,2);
    if (iVar1 != 0) {
      if (iVar7 == 1) {
        if (param_2[1] == 0) {
          param_2[1] = 8;
          *param_2 = *param_2 | 0x200;
        }
        uVar4 = DAT_0000a690 & *param_2;
LAB_0000a51a:
        *param_2 = uVar4;
      }
      else if (iVar7 == 2) {
        if ((*param_2 & 0x600) == 0x200) {
          param_2[1] = 0x10;
          uVar4 = *param_2 | 0x100;
          goto LAB_0000a51a;
        }
        break;
      }
      uVar4 = param_2[2];
      param_2[2] = uVar4 - 1;
      if (uVar4 != 0) {
        pbVar5 = (byte *)*param_3;
        *param_3 = (int)(pbVar5 + 1);
        *(byte *)local_3c = *pbVar5;
        iVar1 = param_3[1];
        local_3c = (uint *)((int)local_3c + 1);
        param_3[1] = iVar1 + -1;
        if ((iVar1 + -1 < 1) && (iVar1 = (*(code *)param_2[0x60])(param_1,param_3), iVar1 != 0)) {
          iVar7 = 0;
          goto LAB_0000a606;
        }
      }
    }
    iVar7 = iVar7 + 1;
  } while (iVar7 != 3);
  if (param_2[1] == 0) {
    param_2[1] = 10;
  }
  iVar7 = 0;
  FUN_0000a69c(param_2[5],(0x10 - param_2[1]) + DAT_0000a694);
  while( true ) {
    if (param_2[2] == 0) break;
    pbVar5 = (byte *)*param_3;
    uVar4 = (uint)*pbVar5;
    if (*(char *)(param_2[5] + uVar4) == '\0') break;
    if ((uVar4 == 0x30) && ((*param_2 & 0x800) != 0)) {
      iVar7 = iVar7 + 1;
      if (local_38 != 0) {
        local_38 = local_38 + -1;
        param_2[2] = param_2[2] + 1;
      }
    }
    else {
      *param_2 = DAT_0000a698 & *param_2;
      *(byte *)local_3c = *pbVar5;
      local_3c = (uint *)((int)local_3c + 1);
    }
    iVar1 = param_3[1];
    param_3[1] = iVar1 + -1;
    if (iVar1 + -1 < 1) {
      iVar1 = (*(code *)param_2[0x60])(param_1,param_3);
      if (iVar1 != 0) break;
    }
    else {
      *param_3 = *param_3 + 1;
    }
    param_2[2] = param_2[2] - 1;
  }
LAB_0000a606:
  if ((int)(*param_2 << 0x17) < 0) {
    if (puVar3 < local_3c) {
      local_3c = (uint *)((int)local_3c + -1);
      (*(code *)param_2[0x5f])(param_1,*(byte *)local_3c,param_3);
    }
    if (local_3c == puVar3) {
      return 1;
    }
  }
  uVar4 = *param_2 & 0x10;
  if ((*param_2 & 0x10) == 0) {
    *(byte *)local_3c = (byte)uVar4;
    uVar2 = (*local_30)(param_1,puVar3,uVar4,param_2[1]);
    puVar6 = (undefined4 *)*param_4;
    if (((int)(*param_2 << 0x1a) < 0) || (-1 < (int)(*param_2 << 0x1f))) {
      *param_4 = puVar6 + 1;
      *(undefined4 *)*puVar6 = uVar2;
    }
    else {
      *param_4 = puVar6 + 1;
      *(short *)*puVar6 = (short)uVar2;
    }
    param_2[3] = param_2[3] + 1;
  }
  param_2[4] = (uint)((int)local_3c + param_2[4] + (iVar7 - (int)puVar3));
  return 0;
}


