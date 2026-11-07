/* UNREVIEWED Ghidra output: FUN_00007c54 @ 00007c54 */

longlong FUN_00007c54(uint param_1,int param_2,undefined4 param_3)

{
  undefined2 uVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  uint local_20;
  uint uStack_1c;
  undefined4 uStack_18;
  
  local_20 = param_1;
  uStack_1c = param_2;
  uStack_18 = param_3;
  iVar2 = FUN_00007a68(param_1 & 0xff);
  iVar4 = DAT_00007d20;
  if (iVar2 == 0) {
    iVar3 = FUN_000098dc(DAT_00007d20,0x2f);
    if (iVar3 != 0) {
      iVar4 = FUN_000098dc(iVar4,0x2f);
      iVar4 = iVar4 + 1;
    }
    FUN_00002678(iVar4,0x15,DAT_00007d24);
  }
  iVar4 = DAT_00007d20;
  if (param_2 == 0) {
    iVar3 = FUN_000098dc(DAT_00007d20,0x2f);
    if (iVar3 != 0) {
      iVar4 = FUN_000098dc(iVar4,0x2f);
      iVar4 = iVar4 + 1;
    }
    FUN_00002678(iVar4,0x16,DAT_00007d28);
  }
  iVar4 = DAT_00007d2c;
  iVar3 = *(int *)(iVar2 + 4);
  *(undefined4 *)(iVar3 + DAT_00007d2c) = DAT_00007d30;
  *(undefined4 *)(iVar3 + iVar4 + -4) = DAT_00007d34;
  local_20 = *DAT_00007d38;
  uStack_1c = DAT_00007d38[1];
  FUN_0000930c(iVar3,&local_20,&uStack_18,DAT_00007d38 + 2);
  iVar2 = *(int *)(iVar2 + 4);
  *(uint *)(iVar2 + DAT_00007d3c) =
       (*(uint *)(iVar2 + DAT_00007d3c) ^ 0x100000) & DAT_00007d40 ^ *(uint *)(iVar2 + DAT_00007d3c)
  ;
  iVar4 = DAT_00007d4c;
  *(uint *)(iVar2 + DAT_00007d44) = *(uint *)(iVar2 + DAT_00007d44) & DAT_00007d48;
  *(undefined4 *)(iVar2 + DAT_00007d50) = 0x1a;
  *(uint *)(iVar2 + 0x1100) = *(uint *)(iVar2 + 0x1100) | 0x10000;
  FUN_00009748(iVar4 + 4,param_2,7);
  uVar1 = *(undefined2 *)(param_2 + 4);
  *(char *)(iVar4 + 0xc) = (char)((ushort)uVar1 >> 8);
  *(char *)(iVar4 + 0xb) = (char)uVar1;
  *(undefined1 *)(iVar4 + 0xd) = 0;
  *(undefined1 *)(iVar4 + 0xe) = 0;
  return (ulonglong)local_20 << 0x20;
}


