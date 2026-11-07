/* UNREVIEWED Ghidra output: FUN_0000860c @ 0000860c */

undefined8 FUN_0000860c(undefined4 param_1,int param_2,int param_3,uint param_4)

{
  int iVar1;
  int iVar2;
  int iVar3;
  uint uVar4;
  undefined4 uVar5;
  int iVar6;
  
  iVar1 = FUN_00007ad4();
  iVar3 = DAT_00008768;
  if (iVar1 == 0) {
    iVar2 = FUN_000098dc(DAT_00008768,0x2f);
    if (iVar2 != 0) {
      iVar3 = FUN_000098dc(iVar3,0x2f);
      iVar3 = iVar3 + 1;
    }
    FUN_00002678(iVar3,0xce,DAT_0000876c);
  }
  iVar3 = DAT_00008768;
  if (*DAT_00008770 != '\0') {
    iVar2 = FUN_000098dc(DAT_00008768,0x2f);
    if (iVar2 != 0) {
      iVar3 = FUN_000098dc(iVar3,0x2f);
      iVar3 = iVar3 + 1;
    }
    FUN_00002678(iVar3,0xcf,DAT_00008774);
  }
  FUN_00007b78(0xd);
  iVar3 = DAT_00008778;
  do {
    iVar2 = DAT_00008790;
    iVar6 = *(int *)(iVar1 + 4);
    if ((*(uint *)(iVar6 + DAT_0000877c) & 0x20) != 0) {
      *(uint *)(iVar6 + DAT_0000878c) =
           ((param_2 << 1 | 1U) ^ *(uint *)(iVar6 + DAT_0000878c)) & 0x7ff ^
           *(uint *)(iVar6 + DAT_0000878c);
      uVar4 = *(uint *)(iVar6 + iVar2);
      *(uint *)(iVar6 + iVar2) = ((param_4 << 0x10 | 7) ^ uVar4) & DAT_00008794 ^ uVar4;
      FUN_00007b78(0xe);
      iVar3 = DAT_00008778;
      goto LAB_0000874e;
    }
    iVar3 = iVar3 + -1;
    FUN_00007ae8(0x20);
  } while (iVar3 != 0);
  uVar5 = 0xd;
  goto LAB_000086f2;
  while( true ) {
    iVar3 = iVar3 + -1;
    FUN_00007ae8(0x20);
    if (iVar3 == 0) break;
LAB_0000874e:
    if ((*(uint *)(*(int *)(iVar1 + 4) + DAT_0000877c) & 0x40) != 0) {
      uVar4 = 0;
      goto LAB_0000868e;
    }
  }
  uVar5 = 0xe;
  goto LAB_000086f2;
LAB_0000868e:
  if (param_4 <= uVar4) goto LAB_000086ce;
  FUN_00007b78(0xf);
  iVar3 = DAT_00008778;
  while( true ) {
    if (((*(uint *)(*(int *)(iVar1 + 4) + DAT_00008780) & 0xf) != 0) || (*DAT_00008784 != '\0'))
    break;
    iVar3 = iVar3 + -1;
    FUN_00007ae8(0x20);
    if (iVar3 == 0) {
      uVar5 = 0xf;
      goto LAB_000086f2;
    }
  }
  if (*DAT_00008784 != '\0') {
    uVar4 = 0xffffffff;
    goto LAB_000086d0;
  }
  *(char *)(param_3 + uVar4) = (char)*(undefined4 *)(*(int *)(iVar1 + 4) + DAT_00008788);
  uVar4 = uVar4 + 1 & 0xff;
  goto LAB_0000868e;
LAB_000086ce:
  uVar4 = 0;
LAB_000086d0:
  FUN_00007b78(0x10);
  iVar3 = DAT_00008778;
  do {
    if ((*(uint *)(*(int *)(iVar1 + 4) + DAT_0000877c) & 0x40) == 0) {
      FUN_000093d0();
      if (*DAT_00008784 == '\0') {
        uVar4 = param_4;
      }
      goto LAB_0000870a;
    }
    iVar3 = iVar3 + -1;
    FUN_00007ae8(0x20);
  } while (iVar3 != 0);
  uVar5 = 0x10;
LAB_000086f2:
  uVar4 = FUN_000082b4(iVar1,uVar5);
LAB_0000870a:
  return CONCAT44(param_4,uVar4);
}


