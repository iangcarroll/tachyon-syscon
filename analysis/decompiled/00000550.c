/* UNREVIEWED Ghidra output: FUN_00000550 @ 00000550 */

undefined8 FUN_00000550(uint param_1,uint param_2,uint param_3,uint param_4,uint *param_5)

{
  int iVar1;
  int iVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint uVar7;
  uint uVar8;
  bool bVar9;
  uint local_30;
  uint local_2c;
  
  if ((param_2 <= param_4 && param_4 != param_2) || ((param_4 == param_2 && (param_1 < param_3)))) {
    local_30 = 0;
    local_2c = 0;
    goto LAB_000005d4;
  }
  iVar1 = FUN_0000240c(param_3,param_4);
  iVar2 = FUN_0000240c(param_1,param_2);
  uVar4 = iVar1 - iVar2;
  uVar5 = uVar4 - 0x20;
  if ((int)uVar5 < 0) {
    uVar6 = param_4 << (uVar4 & 0xff) | param_3 >> (0x20 - uVar4 & 0xff);
    param_3 = param_3 << (uVar4 & 0xff);
    if (uVar6 <= param_2) goto LAB_0000059c;
LAB_00000612:
    local_30 = 0;
    local_2c = 0;
  }
  else {
    uVar6 = param_3 << (uVar5 & 0xff);
    param_3 = param_3 << (uVar4 & 0xff);
    if (param_2 < uVar6) goto LAB_00000612;
LAB_0000059c:
    if ((uVar6 == param_2) && (param_1 < param_3)) goto LAB_00000612;
    bVar9 = param_1 < param_3;
    param_1 = param_1 - param_3;
    param_2 = (param_2 - uVar6) - (uint)bVar9;
    if ((int)uVar5 < 0) {
      local_2c = 1 >> (0x20 - uVar4 & 0xff);
    }
    else {
      local_2c = 1 << (uVar5 & 0xff);
    }
    local_30 = 1 << (uVar4 & 0xff);
  }
  if (uVar4 == 0) goto LAB_000005d4;
  uVar3 = param_3 >> 1 | uVar6 << 0x1f;
  uVar6 = uVar6 >> 1;
  uVar8 = uVar4;
  do {
    while ((uVar6 <= param_2 && ((uVar6 != param_2 || (uVar3 <= param_1))))) {
      bVar9 = param_1 < uVar3;
      uVar7 = param_1 - uVar3;
      uVar8 = uVar8 - 1;
      param_1 = uVar7 * 2 + 1;
      param_2 = ((param_2 - uVar6) - (uint)bVar9) * 2 + (uint)CARRY4(uVar7,uVar7) +
                (uint)(0xfffffffe < uVar7 * 2);
      if (uVar8 == 0) goto LAB_00000658;
    }
    uVar8 = uVar8 - 1;
    bVar9 = CARRY4(param_1,param_1);
    param_1 = param_1 * 2;
    param_2 = param_2 * 2 + (uint)bVar9;
  } while (uVar8 != 0);
LAB_00000658:
  bVar9 = CARRY4(local_30,param_1);
  uVar6 = local_30 + param_1;
  iVar1 = local_2c + param_2;
  if ((int)uVar5 < 0) {
    param_1 = param_1 >> (uVar4 & 0xff) | param_2 << (0x20 - uVar4 & 0xff);
    param_2 = param_2 >> (uVar4 & 0xff);
    if (-1 < (int)uVar5) goto LAB_0000067c;
LAB_000006d2:
    uVar5 = param_2 << (uVar4 & 0xff) | param_1 >> (0x20 - uVar4 & 0xff);
  }
  else {
    param_1 = param_2 >> (uVar5 & 0xff);
    param_2 = param_2 >> (uVar4 & 0xff);
    if ((int)uVar5 < 0) goto LAB_000006d2;
LAB_0000067c:
    uVar5 = param_1 << (uVar5 & 0xff);
  }
  uVar4 = param_1 << (uVar4 & 0xff);
  local_30 = uVar6 - uVar4;
  local_2c = ((iVar1 + (uint)bVar9) - uVar5) - (uint)(uVar6 < uVar4);
LAB_000005d4:
  if (param_5 != (uint *)0x0) {
    *param_5 = param_1;
    param_5[1] = param_2;
  }
  return CONCAT44(local_2c,local_30);
}


