/* UNREVIEWED Ghidra output: FUN_00007e7c @ 00007e7c */

uint FUN_00007e7c(undefined1 param_1)

{
  int iVar1;
  int iVar2;
  int iVar3;
  
  iVar1 = FUN_00007a68(param_1);
  iVar3 = DAT_00007f10;
  if (iVar1 == 0) {
    iVar2 = FUN_000098dc(DAT_00007f10,0x2f);
    if (iVar2 != 0) {
      iVar3 = FUN_000098dc(iVar3,0x2f);
      iVar3 = iVar3 + 1;
    }
    FUN_00002678(iVar3,0x83,DAT_00007f14);
  }
  iVar2 = *(int *)(iVar1 + 4);
  *(uint *)(iVar2 + 0x1100) = *(uint *)(iVar2 + 0x1100) & 0xfffffffe;
  *(uint *)((*(byte *)(iVar1 + 9) + 0x460) * 4 + iVar2) = *(byte *)(iVar1 + 8) | 0x1000000;
  iVar3 = DAT_00007f18;
  *(uint *)(iVar2 + 0x1100) = *(uint *)(iVar2 + 0x1100) | 1;
  *(uint *)(iVar2 + iVar3) = *(uint *)(iVar2 + iVar3) | 0x100;
  FUN_00007ae8(32000);
  *(uint *)(*(int *)(iVar1 + 4) + iVar3) = *(uint *)(*(int *)(iVar1 + 4) + iVar3) & DAT_00007f1c;
  FUN_00007ae8(0xc80);
  return *(uint *)(*(int *)(iVar1 + 4) + (*(byte *)(iVar1 + 9) + 0x4a0) * 4 + DAT_00007f20) & 0xffff
  ;
}


