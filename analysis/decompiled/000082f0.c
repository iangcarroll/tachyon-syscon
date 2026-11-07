/* UNREVIEWED Ghidra output: FUN_000082f0 @ 000082f0 */

longlong FUN_000082f0(uint param_1,char *param_2)

{
  uint uVar1;
  int *piVar2;
  undefined1 *puVar3;
  int iVar4;
  int iVar5;
  int iVar6;
  undefined4 uVar7;
  char *local_14;
  
  local_14 = param_2;
  puVar3 = (undefined1 *)FUN_00007ad4();
  iVar5 = DAT_00008414;
  if (puVar3 == (undefined1 *)0x0) {
    iVar4 = FUN_000098dc(DAT_00008414,0x2f);
    if (iVar4 != 0) {
      iVar5 = FUN_000098dc(iVar5,0x2f);
      iVar5 = iVar5 + 1;
    }
    FUN_00002678(iVar5,0x57,DAT_00008418);
  }
  iVar5 = DAT_00008414;
  if (param_2 == (char *)0x0) {
    iVar4 = FUN_000098dc(DAT_00008414,0x2f);
    if (iVar4 != 0) {
      iVar5 = FUN_000098dc(iVar5,0x2f);
      iVar5 = iVar5 + 1;
    }
    FUN_00002678(iVar5,0x58,DAT_0000841c);
  }
  iVar5 = DAT_00008420;
  iVar4 = *(int *)(puVar3 + 4);
  *(undefined4 *)(iVar4 + DAT_00008420) = DAT_00008424;
  *(undefined4 *)(iVar4 + iVar5 + -4) = DAT_00008428;
  FUN_00007ae8(1000);
  iVar4 = FUN_00007a54(*puVar3);
  iVar6 = FUN_00007a54(puVar3[2]);
  uVar1 = DAT_00008430;
  iVar5 = DAT_0000842c;
  iVar4 = (uint)*(byte *)(iVar4 + 5) * 4 + DAT_0000842c;
  *(uint *)(iVar4 + 4) = (byte)puVar3[1] | DAT_00008430;
  uVar7 = *(undefined4 *)(puVar3 + 4);
  iVar5 = (uint)*(byte *)(iVar6 + 5) * 4 + iVar5;
  *(uint *)(iVar5 + 4) = uVar1 | (byte)puVar3[3];
  *(uint *)(iVar4 + 4) = *(uint *)(iVar4 + 4) | 0x2000000;
  *(uint *)(iVar5 + 4) = *(uint *)(iVar5 + 4) | 0x2000000;
  uVar1 = (uint)local_14 >> 8;
  local_14 = (char *)CONCAT31((uint3)uVar1 & 0xffff00,8);
  FUN_0000934c(uVar7,&local_14);
  iVar4 = *(int *)(puVar3 + 4);
  *(undefined4 *)(iVar4 + DAT_00008434) = 7;
  *(uint *)(iVar4 + 0x1200) = *(uint *)(iVar4 + 0x1200) | 0x600;
  *(uint *)(iVar4 + 0x1200) = *(uint *)(iVar4 + 0x1200) | 0x100;
  *(undefined4 *)(iVar4 + DAT_00008438) = 0;
  iVar5 = DAT_0000843c;
  *(uint *)(iVar4 + DAT_0000843c) = *(uint *)(iVar4 + DAT_0000843c) | 4;
  if (*param_2 == '\0') {
    *DAT_00008440 = 0;
    *(uint *)(iVar4 + DAT_00008444) = *(uint *)(iVar4 + DAT_00008444) | 0x480;
    *(uint *)(iVar4 + iVar5) = *(uint *)(iVar4 + iVar5) | 1;
  }
  piVar2 = DAT_00008448;
  if (-1 < (char)puVar3[8]) {
    iVar5 = 1 << ((int)(char)puVar3[8] & 0x1fU);
    DAT_00008448[0x60] = iVar5;
    *piVar2 = iVar5;
  }
  return (ulonglong)param_1 << 0x20;
}


