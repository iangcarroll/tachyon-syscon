/* UNREVIEWED Ghidra output: FUN_0000386c @ 0000386c */

undefined4 FUN_0000386c(uint param_1,char *param_2)

{
  byte bVar1;
  int iVar2;
  int iVar3;
  uint uVar4;
  uint uVar5;
  byte local_19 [5];
  
  iVar3 = DAT_00003934;
  if (*DAT_00003930 == '\0') {
    iVar2 = FUN_000098dc(DAT_00003934,0x2f);
    if (iVar2 != 0) {
      iVar3 = FUN_000098dc(iVar3,0x2f);
      iVar3 = iVar3 + 1;
    }
    FUN_00002678(iVar3,0x6c,DAT_00003938);
  }
  iVar3 = DAT_00003934;
  if ((param_2 == (char *)0x0) || (0xf < param_1)) {
    iVar2 = FUN_000098dc(DAT_00003934,0x2f);
    if (iVar2 != 0) {
      iVar3 = FUN_000098dc(iVar3,0x2f);
      iVar3 = iVar3 + 1;
    }
    FUN_00002678(iVar3,0x6d,DAT_0000393c);
  }
  uVar4 = 1 << (param_1 & 7);
  uVar5 = uVar4 & 0xff;
  iVar3 = (param_1 >> 3) + 6;
  FUN_000036bc(iVar3,local_19);
  bVar1 = (byte)uVar4;
  if (*param_2 == '\0') {
    if ((local_19[0] & uVar5) != 0) {
      return 0;
    }
    local_19[0] = bVar1 | local_19[0];
  }
  else {
    if (param_2[2] != '\0') {
      FUN_0000379c(param_1,param_2[1]);
    }
    if ((uVar5 & local_19[0]) == 0) {
      return 0;
    }
    local_19[0] = local_19[0] & ~bVar1;
  }
  FUN_0000374c(iVar3,local_19[0]);
  FUN_000036bc(iVar3,local_19);
  return 0;
}


