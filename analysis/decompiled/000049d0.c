/* UNREVIEWED Ghidra output: FUN_000049d0 @ 000049d0 */

void FUN_000049d0(undefined1 *param_1)

{
  char cVar1;
  int iVar2;
  uint uVar3;
  int iVar4;
  undefined4 uVar5;
  uint uVar6;
  undefined1 *puVar7;
  char *pcVar8;
  uint uVar9;
  undefined4 uVar10;
  code *pcVar11;
  int local_a4;
  char *local_a0;
  char local_98 [132];
  
LAB_000049d6:
  while( true ) {
    while( true ) {
      do {
        iVar2 = FUN_00008cf0(*param_1);
        if (iVar2 == 0) {
          return;
        }
        uVar3 = FUN_00008de4(*param_1);
        iVar2 = DAT_00004bd8;
        if ((int)uVar3 < 0) {
          iVar4 = FUN_000098dc(DAT_00004bd8,0x2f);
          if (iVar4 != 0) {
            iVar2 = FUN_000098dc(iVar2,0x2f);
            iVar2 = iVar2 + 1;
          }
          FUN_00002678(iVar2,DAT_00004be0,DAT_00004bdc);
        }
      } while ((param_1[0xd] == '\0') || (uVar9 = uVar3 & 0xff, 0x74 < uVar9 - 10));
      if (*(int *)(param_1 + 8) == 0) {
        FUN_00008f88(3,DAT_00004be8,DAT_00004be4);
      }
      if ((*DAT_00004bec != '\0') && (*(int *)(param_1 + 0x10) != DAT_00004bf0)) {
        FUN_00008f88(1,DAT_00004be8,DAT_00004bf4,uVar3 & 0xff,uVar3);
      }
      if (param_1[0xc] != '\0') {
        FUN_00008c34(*param_1,uVar9);
      }
      uVar10 = DAT_00004bf8;
      uVar6 = *(uint *)(param_1 + 8);
      if (uVar6 < 0x7d) break;
      *(undefined1 *)(*(int *)(param_1 + 4) + 0x7f) = 0;
      FUN_00003f08(*(undefined4 *)(param_1 + 4),uVar10,*(undefined4 *)(param_1 + 0x10));
      *(undefined4 *)(param_1 + 8) = 0;
    }
    if ((uVar9 == 10) || (uVar9 == 0xd)) break;
    *(uint *)(param_1 + 8) = uVar6 + 1;
    *(char *)(*(int *)(param_1 + 4) + uVar6) = (char)uVar3;
  }
  if (uVar6 != 0) {
    iVar4 = 0;
    *(undefined1 *)(*(int *)(param_1 + 4) + uVar6) = 0;
    iVar2 = *(int *)(param_1 + 4);
    while( true ) {
      puVar7 = (undefined1 *)(iVar2 + iVar4);
      if (*(char *)(iVar2 + iVar4) == '\0') break;
      if (*(char *)(iVar2 + iVar4) == ' ') {
        *(undefined1 *)(iVar2 + iVar4) = 0x3a;
      }
      iVar4 = iVar4 + 1;
    }
    if ((iVar4 != 0) && ((puVar7[-1] != ';' || (puVar7[-2] != ':')))) {
      *puVar7 = 0x3a;
      puVar7[1] = 0x3b;
      puVar7[2] = 0;
    }
    uVar10 = *(undefined4 *)(param_1 + 4);
    pcVar11 = *(code **)(param_1 + 0x10);
    iVar2 = FUN_00009828(uVar10,0x3a);
    if (iVar2 == 0) {
LAB_00004ae2:
      local_a0 = (char *)0x0;
    }
    else {
      local_a0 = (char *)(iVar2 + 1);
      iVar2 = FUN_00009828(local_a0,0x3a);
      if (iVar2 == 0) goto LAB_00004ae2;
    }
    local_a4 = 0;
    while( true ) {
      iVar4 = DAT_00004bfc + local_a4 * 0xe;
      pcVar8 = (char *)CONCAT13(*(undefined1 *)(iVar4 + 3),
                                CONCAT12(*(undefined1 *)(iVar4 + 2),
                                         CONCAT11(*(undefined1 *)(iVar4 + 1),
                                                  *(undefined1 *)(local_a4 * 0xe + DAT_00004bfc))));
      uVar5 = FUN_00002650(pcVar8);
      iVar2 = FUN_00009844(uVar10,pcVar8,uVar5);
      if (iVar2 == 0) break;
      local_a4 = local_a4 + 1;
      if (local_a4 == 0x25) goto code_r0x00004bc2;
    }
    cVar1 = *(char *)(iVar4 + 8);
    if (cVar1 == '\x01') {
      if (local_a0 == (char *)0x0) {
        uVar5 = DAT_00004c04;
        goto LAB_00004b3c;
      }
    }
    else {
      if ((cVar1 != '\x03') && (pcVar8 = local_a0, cVar1 == '\0')) {
        if (local_a0 == (char *)0x0) goto LAB_00004b82;
        uVar5 = DAT_00004c00;
        goto LAB_00004b3c;
      }
      local_a0 = pcVar8;
      if (local_a0 == (char *)0x0) goto LAB_00004b82;
    }
    if (*(char *)(DAT_00004bfc + local_a4 * 0xe + 9) != '\0') {
      FUN_000098b4(local_98,local_a0,0x7f);
      for (pcVar8 = local_98; *pcVar8 != '\0'; pcVar8 = pcVar8 + 1) {
        cVar1 = FUN_00009a40();
        *pcVar8 = cVar1;
      }
      local_a0 = local_98;
    }
LAB_00004b82:
    iVar2 = (**(code **)(DAT_00004bfc + local_a4 * 0xe + 4))(local_a0,pcVar11);
    uVar10 = DAT_00004c08;
    if (iVar2 == 0) {
      uVar10 = DAT_00004c0c;
    }
    (*pcVar11)(uVar10);
  }
  goto LAB_00004bb2;
code_r0x00004bc2:
  uVar5 = DAT_00004c10;
LAB_00004b3c:
  FUN_00003f08(uVar10,uVar5,pcVar11);
LAB_00004bb2:
  *(undefined4 *)(param_1 + 8) = 0;
  goto LAB_000049d6;
}


