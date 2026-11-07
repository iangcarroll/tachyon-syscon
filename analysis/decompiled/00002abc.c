/* UNREVIEWED Ghidra output: FUN_00002abc @ 00002abc */

int FUN_00002abc(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,
                undefined1 param_5,undefined4 param_6,undefined1 param_7,undefined1 param_8)

{
  int iVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  undefined4 uVar5;
  int iVar6;
  uint uVar7;
  undefined4 uVar8;
  int iVar9;
  char *pcVar10;
  uint uVar11;
  undefined1 *puVar12;
  undefined1 uStack00000000;
  undefined1 uStack0000002a;
  undefined1 uStack0000002c;
  undefined1 uStack0000004a;
  undefined1 uStack0000004b;
  undefined1 uStack00000069;
  uint auStack_214 [128];
  
  uVar5 = DAT_00002c90;
  iVar4 = DAT_00002c8c;
  iVar9 = DAT_00002c8c + 0x200;
  iVar1 = DAT_00002c8c + 0x200;
  iVar2 = DAT_00002c8c + 0x200;
  iVar3 = DAT_00002c8c + 0x200;
  *(undefined4 *)((int)auStack_214 + DAT_00002c8c + 0x210) = param_1;
  puVar12 = &uStack0000002c + DAT_00002c8c;
  FUN_00008f88(3,DAT_00002c90,DAT_00002c98,DAT_00002c94 - ((int)auStack_214 + DAT_00002c8c + 0x200))
  ;
  FUN_000079d0();
  FUN_000098b4(puVar12,param_2,0x1e);
  (&uStack0000004a)[iVar4] = 0;
  FUN_000098b4(&uStack0000004b + iVar4,param_3,0x1e);
  (&uStack00000069)[iVar4] = 0;
  *(undefined4 *)((int)auStack_214 + iVar9) = param_3;
  FUN_00008f88(3,uVar5,DAT_00002c9c,param_2);
  iVar9 = *(int *)((int)auStack_214 + iVar4 + 0x210);
  pcVar10 = (char *)(iVar9 + 0x380);
  iVar9 = iVar9 + 0x3a0;
  *(undefined4 *)((int)auStack_214 + iVar4 + 0x20c) = 1;
  *(undefined4 *)(&param_5 + iVar4) = 0xe;
  do {
    if ((((*pcVar10 != -1) && (iVar6 = FUN_000027dc(pcVar10), iVar6 != 0)) &&
        (uVar7 = FUN_0000282c(pcVar10), (byte)pcVar10[0x1f] == uVar7)) &&
       (uVar7 = FUN_0000282c(iVar9), *(byte *)(iVar9 + 0x1f) == uVar7)) {
      uVar7 = 0;
      FUN_000098b4(&param_8 + iVar4,pcVar10,0x1e);
      (&uStack0000002a)[iVar4] = 0;
      do {
        iVar6 = FUN_00009890(&uStack0000002c + uVar7 * 0x3e + iVar4,&param_8 + iVar4,0x1e);
        if (iVar6 == 0) goto LAB_00002bd4;
        uVar7 = uVar7 + 1;
      } while ((uVar7 & 0xff) < *(uint *)((int)auStack_214 + iVar4 + 0x20c));
      uVar7 = *(uint *)((int)auStack_214 + iVar4 + 0x20c);
      uVar11 = uVar7 + 1 & 0xff;
      if (7 < uVar7) {
        *(undefined4 *)((int)auStack_214 + iVar4 + 0x204) = 0xf;
        *(undefined4 *)((int)auStack_214 + iVar1) = 8;
        FUN_00008f88(1,DAT_00002c90,DAT_00002ca0,uVar11);
        return 0;
      }
      *(int *)((int)auStack_214 + iVar4 + 0x20c) = *(int *)((int)auStack_214 + iVar4 + 0x20c) * 0x3e
      ;
      puVar12 = &uStack0000002c + *(int *)((int)auStack_214 + iVar4 + 0x20c) + iVar4;
      FUN_000098b4(puVar12,&param_8 + iVar4,0x1e);
      iVar6 = *(int *)((int)auStack_214 + iVar4 + 0x20c);
      puVar12[0x1e] = 0;
      FUN_000098b4(&uStack0000004b + iVar6 + iVar4,iVar9,0x1e);
      puVar12[0x3d] = 0;
      *(uint *)((int)auStack_214 + iVar4 + 0x20c) = uVar11;
    }
LAB_00002bd4:
    if ((*(uint *)(&param_5 + iVar4) & 3) == 0) {
      FUN_000079d0();
    }
    uVar5 = DAT_00002c90;
    iVar6 = *(int *)(&param_5 + iVar4);
    pcVar10 = pcVar10 + -0x40;
    iVar9 = iVar9 + -0x40;
    *(int *)(&param_5 + iVar4) = iVar6 + -1;
    if (iVar6 == 0) {
      FUN_00008f88(3,DAT_00002c90,DAT_00002ca4,*(undefined4 *)((int)auStack_214 + iVar4 + 0x20c));
      FUN_000079d0();
      iVar9 = FUN_000027a8(*(undefined4 *)((int)auStack_214 + iVar4 + 0x210),0x3c0);
      if (iVar9 == 0) {
        FUN_00008f88(1,uVar5,DAT_00002ca8);
      }
      else {
        FUN_000079d0();
        uVar7 = 0;
        puVar12 = &uStack0000002c + iVar4;
        while( true ) {
          *(undefined1 **)((int)auStack_214 + iVar2) = &param_7 + iVar4;
          uVar8 = *(undefined4 *)((int)auStack_214 + iVar4 + 0x210);
          *(undefined4 *)(&param_7 + iVar4) = 0;
          iVar9 = FUN_000029a0(uVar8,0x3c0,0,0);
          if (iVar9 == 0) {
            FUN_00008f88(1,uVar5,DAT_00002cac,uVar7);
            return 0;
          }
          iVar9 = FUN_000028d4(*(undefined4 *)(&param_7 + iVar4),puVar12,puVar12 + 0x1f);
          if (iVar9 == 0) break;
          FUN_000079d0();
          uVar7 = uVar7 + 1;
          puVar12 = puVar12 + 0x3e;
          if (*(uint *)((int)auStack_214 + iVar4 + 0x20c) <= (uVar7 & 0xff)) {
            FUN_00008f88(3,uVar5,DAT_00002cb4,*(undefined4 *)((int)auStack_214 + iVar4 + 0x20c));
            return iVar9;
          }
        }
        *(undefined1 **)((int)auStack_214 + iVar3) = puVar12;
        FUN_00008f88(1,uVar5,DAT_00002cb0,uVar7);
      }
      return 0;
    }
  } while( true );
}


