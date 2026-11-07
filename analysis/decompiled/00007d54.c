/* UNREVIEWED Ghidra output: FUN_00007d54 @ 00007d54 */

int FUN_00007d54(void)

{
  char cVar1;
  char *pcVar2;
  int iVar3;
  undefined4 uVar4;
  uint uVar5;
  int iVar6;
  uint uVar7;
  int iVar8;
  undefined1 local_28;
  char local_27;
  undefined2 local_24 [8];
  
  iVar8 = DAT_00007e44;
  iVar6 = DAT_00007e40;
  pcVar2 = DAT_00007e3c;
  cVar1 = *DAT_00007e3c;
  if (cVar1 == '\0') {
    *(undefined4 *)(DAT_00007e40 + DAT_00007e44) = DAT_00007e48;
    *(undefined4 *)(iVar6 + iVar8 + -4) = DAT_00007e4c;
    local_28 = 8;
    local_27 = cVar1;
    FUN_00009688(iVar6,&local_28);
    FUN_0000975a(local_24,0,0xc);
    local_24[0] = (undefined2)DAT_00007e50;
    FUN_00009664(iVar6,local_24);
    *pcVar2 = '\x01';
  }
  iVar8 = 100;
  do {
    iVar3 = DAT_00007e54;
    if ((*(uint *)(iVar6 + DAT_00007e54) & 1) != 0) break;
    iVar8 = iVar8 + -1;
    FUN_00007ae8(0x140);
  } while (iVar8 != 0);
  uVar4 = DAT_00007e5c;
  iVar8 = DAT_00007e58;
  if ((*(uint *)(iVar6 + iVar3) & 1) != 0) {
    *(uint *)(DAT_00007e58 + 0x1100) = *(uint *)(DAT_00007e58 + 0x1100) & 0xfffffffe;
    *(undefined4 *)(iVar8 + 0x1180) = uVar4;
    *(uint *)(iVar8 + 0x1100) = *(uint *)(iVar8 + 0x1100) | 1;
    *(uint *)(iVar8 + iVar3) = *(uint *)(iVar8 + iVar3) | 0x100;
    FUN_00007ae8(32000);
    *(uint *)(iVar8 + iVar3) = *(uint *)(iVar8 + iVar3) & DAT_00007e60;
    FUN_00007ae8(0xc80);
    iVar6 = DAT_00007e68;
    uVar5 = *(uint *)(iVar8 + DAT_00007e64);
    uVar7 = *(uint *)(DAT_00007e68 + 0x1300);
    *(undefined4 *)(DAT_00007e68 + 0x1300) = 5;
    iVar8 = *(int *)(DAT_00007e6c + 0x3c);
    *(uint *)(iVar6 + 0x1300) = uVar7 & 7;
    if ((iVar8 != 0) && (iVar8 != DAT_00007e70)) {
      iVar6 = FUN_000001fc(((uVar5 & 0xffff) - iVar8) * DAT_00007e74,DAT_00007e78);
      return iVar6 + 300;
    }
  }
  return -0x80000000;
}


