/* UNREVIEWED Ghidra output: FUN_0000a714 @ 0000a714 */

uint FUN_0000a714(undefined4 *param_1,byte *param_2,undefined4 *param_3,int param_4)

{
  uint uVar1;
  uint uVar2;
  int extraout_r1;
  uint uVar3;
  byte *pbVar4;
  byte *pbVar5;
  int iVar6;
  uint uVar7;
  byte bVar8;
  byte *local_2c;
  
  pbVar5 = param_2;
  do {
    pbVar4 = pbVar5;
    uVar7 = (uint)*pbVar4;
    pbVar5 = pbVar4 + 1;
    bVar8 = *(byte *)(DAT_0000a824 + uVar7) & 8;
  } while ((*(byte *)(DAT_0000a824 + uVar7) & 8) != 0);
  if (uVar7 == 0x2d) {
    bVar8 = 1;
    uVar7 = (uint)*pbVar5;
    pbVar5 = pbVar4 + 2;
  }
  else if (uVar7 == 0x2b) {
    uVar7 = (uint)*pbVar5;
    pbVar5 = pbVar4 + 2;
  }
  if (param_4 == 0) {
    if (uVar7 != 0x30) {
      param_4 = 10;
      goto LAB_0000a762;
    }
  }
  else if ((param_4 != 0x10) || (uVar7 != 0x30)) goto LAB_0000a762;
  if ((*pbVar5 & 0xdf) == 0x58) {
    param_4 = 0x10;
    uVar7 = (uint)pbVar5[1];
    pbVar5 = pbVar5 + 2;
  }
  else {
    uVar7 = 0x30;
    if (param_4 == 0) {
      param_4 = 8;
    }
  }
LAB_0000a762:
  uVar1 = FUN_000000e8(0xffffffff,param_4);
  FUN_000001f4(0xffffffff,param_4);
  iVar6 = 0;
  uVar2 = 0;
  do {
    uVar3 = uVar7 - 0x30;
    if (9 < uVar3) {
      if (uVar7 - 0x41 < 0x1a) {
        uVar3 = uVar7 - 0x37;
      }
      else {
        if (0x19 < uVar7 - 0x61) break;
        uVar3 = uVar7 - 0x57;
      }
    }
    if (param_4 <= (int)uVar3) break;
    if (iVar6 < 0) {
      iVar6 = -1;
    }
    else {
      iVar6 = -1;
      if ((uVar2 <= uVar1) && ((uVar1 != uVar2 || (iVar6 = -1, (int)uVar3 <= extraout_r1)))) {
        iVar6 = 1;
        uVar2 = uVar3 + param_4 * uVar2;
      }
    }
    uVar7 = (uint)*pbVar5;
    pbVar5 = pbVar5 + 1;
  } while( true );
  if (iVar6 < 0) {
    uVar2 = 0xffffffff;
    *param_1 = 0x22;
    if (param_3 == (undefined4 *)0x0) {
      return 0xffffffff;
    }
  }
  else {
    if (bVar8 != 0) {
      uVar2 = -uVar2;
    }
    if (param_3 == (undefined4 *)0x0) {
      return uVar2;
    }
    local_2c = param_2;
    if (iVar6 == 0) goto LAB_0000a808;
  }
  local_2c = pbVar5 + -1;
LAB_0000a808:
  *param_3 = local_2c;
  return uVar2;
}


