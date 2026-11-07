/* UNREVIEWED Ghidra output: FUN_00005cac @ 00005cac */

undefined8 FUN_00005cac(undefined4 param_1,undefined4 param_2)

{
  byte bVar1;
  byte bVar2;
  byte *pbVar3;
  byte *pbVar4;
  undefined4 uVar5;
  int iVar6;
  uint uVar7;
  undefined4 local_1c;
  
  if (*DAT_00005da4 != 0) {
    iVar6 = *DAT_00005da4 + -1;
    *DAT_00005da4 = iVar6;
    if (iVar6 == 0) {
      FUN_00005c68(*DAT_00005da8);
    }
  }
  pbVar3 = DAT_00005dac;
  bVar1 = *DAT_00005dac;
  uVar7 = (uint)bVar1;
  if (uVar7 == 1) {
    bVar2 = DAT_00005dac[4];
    local_1c = FUN_0000139c(bVar2);
    uVar5 = FUN_00000a24(local_1c,DAT_00005db0);
    if (pbVar3[0xc] == 0) {
      iVar6 = FUN_0000040c(*(undefined4 *)(pbVar3 + 8),uVar5);
      if (iVar6 == 0) {
        uVar5 = FUN_00001000(*(undefined4 *)(pbVar3 + 8),uVar5);
LAB_00005d26:
        *(undefined4 *)(pbVar3 + 8) = uVar5;
      }
      else {
        pbVar3[8] = 0;
        pbVar3[9] = 0;
        pbVar3[10] = 0;
        pbVar3[0xb] = 0;
        pbVar3[0xc] = bVar1;
      }
    }
    else {
      uVar5 = FUN_000006e8();
      *(undefined4 *)(pbVar3 + 8) = uVar5;
      iVar6 = FUN_0000040c(local_1c,*(undefined4 *)(pbVar3 + 8));
      if (iVar6 != 0) {
        uVar5 = FUN_00001438(bVar2);
        *(undefined4 *)(pbVar3 + 8) = uVar5;
        pbVar3[0xc] = 0;
      }
    }
  }
  else {
    local_1c = param_2;
    if (uVar7 - 2 < 2) {
      DAT_00005dac[0xd] = DAT_00005dac[0xd] + 1;
      if ((ushort)((ushort)pbVar3[0xd] * 0x14) < *(ushort *)(pbVar3 + 0xe)) goto LAB_00005d0c;
      pbVar3[0xd] = 0;
      iVar6 = FUN_000003ec(*(undefined4 *)(pbVar3 + 8),0);
      if (iVar6 != 0) {
        uVar5 = FUN_00001438(pbVar3[4]);
        goto LAB_00005d26;
      }
      pbVar3[8] = 0;
      pbVar3[9] = 0;
      pbVar3[10] = 0;
      pbVar3[0xb] = 0;
    }
    else {
      if ((uVar7 != 5) ||
         (DAT_00005dac[0xd] = DAT_00005dac[0xd] + 1, pbVar4 = DAT_00005db4, pbVar3[0xd] < 3))
      goto LAB_00005d0c;
      pbVar3[0xd] = 0;
      if ((byte)(*pbVar4 + 1) < 10) {
        *pbVar4 = *pbVar4 + 1;
      }
      else {
        *pbVar4 = 0;
      }
      iVar6 = DAT_00005db8 + (uint)*pbVar4 * 3;
      bVar1 = *(byte *)(iVar6 + 1);
      bVar2 = *(byte *)(iVar6 + 2);
      pbVar3[1] = *(byte *)((uint)*pbVar4 * 3 + DAT_00005db8);
      pbVar3[2] = bVar1;
      pbVar3[3] = bVar2;
    }
  }
  FUN_00005b48();
LAB_00005d0c:
  return CONCAT44(local_1c,param_1);
}


