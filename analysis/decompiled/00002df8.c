/* UNREVIEWED Ghidra output: FUN_00002df8 @ 00002df8 */

void FUN_00002df8(void)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 uVar3;
  int iVar4;
  uint uVar5;
  uint local_34;
  undefined1 auStack_30 [32];
  
  iVar1 = DAT_00002ed0;
  FUN_00009748(DAT_00002ed0,DAT_00002ed4,0x16);
  uVar2 = DAT_00002ed8;
  FUN_00002d08(DAT_00002ed8,DAT_00002edc,iVar1);
  FUN_00002d08(uVar2,DAT_00002ee0,iVar1 + 1);
  FUN_00002d08(uVar2,DAT_00002ee4,iVar1 + 2);
  FUN_00002d08(uVar2,DAT_00002ee8,iVar1 + 3);
  FUN_00002d08(uVar2,DAT_00002eec,iVar1 + 4);
  FUN_00002d08(uVar2,DAT_00002ef0,iVar1 + 5);
  local_34 = 3;
  FUN_00002d94(uVar2,DAT_00002ef4,&local_34);
  if (local_34 < 0x1f) {
    if (local_34 < 3) {
      local_34 = 3;
    }
  }
  else {
    local_34 = 0x1e;
  }
  *(char *)(iVar1 + 7) = (char)(local_34 >> 8);
  *(char *)(iVar1 + 6) = (char)local_34;
  *(char *)(iVar1 + 8) = (char)(local_34 >> 0x10);
  uVar3 = DAT_00002ef8;
  *(char *)(iVar1 + 9) = (char)(local_34 >> 0x18);
  local_34 = 3;
  FUN_00002d94(uVar2,uVar3,&local_34);
  if (local_34 < 0x1f) {
    uVar5 = local_34;
    if (local_34 < 3) {
      uVar5 = 3;
    }
  }
  else {
    uVar5 = 0x1e;
  }
  *(char *)(iVar1 + 0xb) = (char)(uVar5 >> 8);
  *(char *)(iVar1 + 0xc) = (char)(uVar5 >> 0x10);
  *(char *)(iVar1 + 10) = (char)uVar5;
  *(char *)(iVar1 + 0xd) = (char)(uVar5 >> 0x18);
  iVar4 = FUN_00002cb8(DAT_00002f00,0x400,DAT_00002efc,auStack_30);
  if (iVar4 == 0) {
    FUN_00008f88(1,DAT_00002f08,DAT_00002f04);
  }
  else {
    FUN_000098b4(iVar1 + 0xe,auStack_30,8);
    *(undefined1 *)(iVar1 + 0x15) = 0;
  }
  return;
}


