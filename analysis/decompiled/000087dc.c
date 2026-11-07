/* UNREVIEWED Ghidra output: FUN_000087dc @ 000087dc */

undefined4 FUN_000087dc(undefined4 param_1)

{
  undefined4 uVar1;
  int iVar2;
  int *piVar3;
  int iVar4;
  int iVar5;
  uint uVar6;
  undefined4 local_20;
  undefined2 local_1c;
  undefined1 local_1a;
  
  iVar2 = FUN_00007a90();
  piVar3 = (int *)FUN_00007a54(param_1);
  iVar5 = DAT_000088a0;
  if (iVar2 == 0) {
    iVar4 = FUN_000098dc(DAT_000088a0,0x2f);
    if (iVar4 != 0) {
      iVar5 = FUN_000098dc(iVar5,0x2f);
      iVar5 = iVar5 + 1;
    }
    FUN_00002678(iVar5,0xd,DAT_000088a4);
  }
  iVar5 = DAT_000088a0;
  if (piVar3 == (int *)0x0) {
    iVar4 = FUN_000098dc(DAT_000088a0,0x2f);
    if (iVar4 != 0) {
      iVar5 = FUN_000098dc(iVar5,0x2f);
      iVar5 = iVar5 + 1;
    }
    FUN_00002678(iVar5,0xe,DAT_000088a8);
  }
  uVar1 = DAT_000088ac;
  *(undefined4 *)(*piVar3 + 0x800) = DAT_000088ac;
  *(uint *)((uint)*(byte *)((int)piVar3 + 5) * 4 + DAT_000088b0 + 4) = *(byte *)(iVar2 + 1) | 0x80;
  iVar5 = *(int *)(iVar2 + 4);
  uVar6 = *(uint *)(iVar5 + 0x800) & 1;
  if ((*(uint *)(iVar5 + 0x800) & 1) == 0) {
    *(undefined4 *)(iVar5 + DAT_000088b4) = DAT_000088b8;
    *(undefined4 *)(iVar5 + 0x800) = uVar1;
    FUN_00009400();
    local_20 = 0x100;
    local_1c = (undefined2)uVar6;
    local_1a = (char)uVar6;
    FUN_0000948c(*(undefined4 *)(iVar2 + 4),&local_20);
    iVar5 = DAT_000088bc;
    iVar2 = *(int *)(iVar2 + 4);
    *(undefined4 *)(iVar2 + DAT_000088bc) = 1;
    *(undefined4 *)(iVar2 + iVar5 + -8) = 3;
  }
  return 0;
}


