/* UNREVIEWED Ghidra output: FUN_00007f58 @ 00007f58 */

undefined4 FUN_00007f58(uint param_1,int param_2)

{
  int iVar1;
  int iVar2;
  int *piVar3;
  uint uVar4;
  int iVar5;
  
  iVar2 = DAT_0000802c;
  if (param_2 == 0) {
    iVar1 = FUN_000098dc(DAT_0000802c,0x2f);
    if (iVar1 != 0) {
      iVar2 = FUN_000098dc(iVar2,0x2f);
      iVar2 = iVar2 + 1;
    }
    FUN_00002678(iVar2,0x21,DAT_00008030);
  }
  iVar2 = DAT_0000802c;
  if (0x18 < param_1) {
    iVar1 = FUN_000098dc(DAT_0000802c,0x2f);
    if (iVar1 != 0) {
      iVar2 = FUN_000098dc(iVar2,0x2f);
      iVar2 = iVar2 + 1;
    }
    FUN_00002678(iVar2,0x22,DAT_00008034);
  }
  piVar3 = (int *)FUN_00007a54(param_1 & 0xff);
  iVar1 = 1 << (sbyte)piVar3[1];
  iVar2 = *piVar3;
  *(undefined4 *)(iVar2 + 0x800) = DAT_00008038;
  if (*(char *)(param_2 + 4) == '\0') {
    *(int *)(iVar2 + 0x12e0) = iVar1;
    iVar2 = DAT_0000803c;
    iVar1 = (uint)*(byte *)((int)piVar3 + 5) * 4;
    if (*(char *)(param_2 + 5) == '\x01') {
      uVar4 = DAT_00008040;
    }
    else if (*(char *)(param_2 + 5) == '\x02') {
      uVar4 = DAT_00008044;
    }
    else {
      iVar5 = iVar1 + DAT_0000803c;
      *(undefined4 *)(iVar5 + 4) = DAT_00008048;
      uVar4 = *(uint *)(iVar5 + 4) | 0x2000000;
    }
    *(uint *)(iVar1 + iVar2 + 4) = uVar4;
  }
  else if (*(char *)(param_2 + 4) == '\x01') {
    *(undefined4 *)((uint)*(byte *)((int)piVar3 + 5) * 4 + DAT_0000803c + 4) = 0x81;
    if (*(int *)(param_2 + 8) << 0x1e < 0) {
      if (*(char *)(param_2 + 7) == '\0') {
        iVar5 = 0x12a0;
      }
      else {
        iVar5 = DAT_0000804c;
      }
      *(int *)(iVar2 + iVar5) = iVar1;
    }
    *(int *)(iVar2 + DAT_00008050) = iVar1;
  }
  return 0;
}


