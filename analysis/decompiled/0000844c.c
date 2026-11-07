/* UNREVIEWED Ghidra output: FUN_0000844c @ 0000844c */

uint FUN_0000844c(undefined4 param_1,int param_2,int param_3,uint param_4)

{
  bool bVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  uint uVar5;
  undefined4 uVar6;
  uint uVar7;
  uint uVar8;
  uint uVar9;
  
  iVar2 = FUN_00007ad4();
  iVar4 = DAT_000085dc;
  if (iVar2 == 0) {
    iVar3 = FUN_000098dc(DAT_000085dc,0x2f);
    if (iVar3 != 0) {
      iVar4 = FUN_000098dc(iVar4,0x2f);
      iVar4 = iVar4 + 1;
    }
    FUN_00002678(iVar4,0x8e,DAT_000085e0);
  }
  iVar4 = DAT_000085dc;
  if (*DAT_000085e4 != '\0') {
    iVar3 = FUN_000098dc(DAT_000085dc,0x2f);
    if (iVar3 != 0) {
      iVar4 = FUN_000098dc(iVar4,0x2f);
      iVar4 = iVar4 + 1;
    }
    FUN_00002678(iVar4,0x8f,DAT_000085e8);
  }
  FUN_00007b78(9);
  iVar4 = DAT_000085ec;
  do {
    if ((*(uint *)(*(int *)(iVar2 + 4) + DAT_000085f0) & 0x20) != 0) {
      uVar5 = 0;
      uVar9 = 0;
      bVar1 = false;
      goto LAB_000084e2;
    }
    iVar4 = iVar4 + -1;
    FUN_00007ae8(0x20);
  } while (iVar4 != 0);
  uVar6 = 9;
  goto LAB_00008576;
  while( true ) {
    iVar4 = DAT_000085fc;
    if (!bVar1) {
      iVar3 = *(int *)(iVar2 + 4);
      *DAT_000085f8 = '\0';
      uVar7 = DAT_00008600;
      uVar8 = *(uint *)(iVar3 + iVar4);
      *(uint *)(iVar3 + iVar4) = (param_2 << 1 ^ uVar8) & 0x7ff ^ uVar8;
      *(uint *)(iVar3 + DAT_00008604) =
           ((param_4 << 0x10 | 7) ^ *(uint *)(iVar3 + DAT_00008604)) & uVar7 ^
           *(uint *)(iVar3 + DAT_00008604);
      FUN_00007b78(0xb);
      iVar4 = DAT_000085ec;
      while ((*(uint *)(*(int *)(iVar2 + 4) + DAT_000085f0) & 0x40) == 0) {
        iVar4 = iVar4 + -1;
        FUN_00007ae8(0x20);
        if (iVar4 == 0) {
          uVar6 = 0xb;
          goto LAB_00008576;
        }
      }
    }
    bVar1 = true;
    if (*DAT_000085f8 != '\0') break;
LAB_000084e2:
    if (param_4 <= uVar9) {
      uVar5 = 0;
      goto LAB_0000859e;
    }
    FUN_00007b78(10);
    uVar8 = *(uint *)(*(int *)(iVar2 + 4) + DAT_000085f4) >> 8;
    uVar7 = uVar8 & 0xf;
    if ((uVar8 & 0xf) == 0) {
      if (DAT_00008608 < uVar5) {
        uVar6 = 10;
        goto LAB_00008576;
      }
      FUN_00007ae8(0x20);
      uVar5 = uVar5 + 1;
    }
    else {
      uVar8 = param_4 - uVar9;
      if (uVar7 < (param_4 - uVar9 & 0xff)) {
        uVar8 = uVar7;
      }
      FUN_00009374(*(int *)(iVar2 + 4),param_3 + uVar9,uVar8 & 0xff);
      uVar5 = 0;
      uVar9 = uVar9 + (uVar8 & 0xff) & 0xff;
    }
  }
  FUN_000093a0(*(undefined4 *)(iVar2 + 4));
  uVar5 = 0xffffffff;
LAB_0000859e:
  FUN_00007b78(0xc);
  iVar4 = DAT_000085ec;
  do {
    if ((*(uint *)(*(int *)(iVar2 + 4) + DAT_000085f0) & 0x40) == 0) {
      FUN_000093a0();
      if (*DAT_000085f8 == '\0') {
        return uVar9;
      }
      return uVar5;
    }
    iVar4 = iVar4 + -1;
    FUN_00007ae8(0x20);
  } while (iVar4 != 0);
  uVar6 = 0xc;
LAB_00008576:
  uVar5 = FUN_000082b4(iVar2,uVar6);
  return uVar5;
}


