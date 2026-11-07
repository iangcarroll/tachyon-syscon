/* UNREVIEWED Ghidra output: FUN_000059d8 @ 000059d8 */

void FUN_000059d8(void)

{
  int iVar1;
  int iVar2;
  char *pcVar3;
  undefined4 uVar4;
  uint uVar5;
  uint uVar6;
  uint uVar7;
  byte local_1c;
  byte local_1b;
  byte local_1a;
  
  pcVar3 = DAT_00005a78;
  iVar1 = DAT_00005a70;
  uVar7 = *(uint *)(DAT_00005a70 + 0x1400);
  uVar5 = *(uint *)(DAT_00005a70 + DAT_00005a6c);
  uVar6 = *(uint *)(DAT_00005a70 + DAT_00005a74);
  local_1b = (byte)uVar5;
  local_1a = (byte)uVar6;
  local_1c = (byte)uVar7;
  FUN_00009748(DAT_00005a78,&local_1c,3);
  uVar4 = DAT_00005a7c;
  uVar6 = uVar6 & 0xff;
  FUN_00008f88(3,DAT_00005a7c,DAT_00005a80,uVar7 & 0xff,uVar5 & 0xff,uVar6);
  if (*pcVar3 != '[') {
    FUN_00008f88(1,uVar4,DAT_00005a84,*pcVar3,0x5b,uVar6);
    FUN_0000975a(pcVar3,0,3);
    *pcVar3 = '[';
    FUN_00009748(&local_1c,pcVar3,3);
    *(uint *)(iVar1 + 0x1400) = (uint)local_1c;
    iVar2 = DAT_00005a74;
    *(uint *)(iVar1 + DAT_00005a6c) = (uint)local_1b;
    *(uint *)(iVar1 + iVar2) = (uint)local_1a;
  }
  return;
}


