/* UNREVIEWED Ghidra output: FUN_000088c0 @ 000088c0 */

undefined4 FUN_000088c0(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  int iVar2;
  int iVar3;
  undefined4 extraout_r3;
  undefined4 uVar4;
  
  iVar1 = FUN_00007a90();
  iVar3 = DAT_00008910;
  if (iVar1 == 0) {
    iVar2 = FUN_000098dc(DAT_00008910,0x2f);
    uVar4 = 0;
    if (iVar2 != 0) {
      iVar3 = FUN_000098dc(iVar3,0x2f);
      iVar3 = iVar3 + 1;
      uVar4 = extraout_r3;
    }
    FUN_00002678(iVar3,0x2b,DAT_00008914,uVar4,param_4);
  }
  iVar3 = DAT_00008918;
  iVar2 = *(int *)(iVar1 + 4);
  *(uint *)(iVar2 + DAT_00008918) = *(uint *)(iVar2 + DAT_00008918) & 0xfffffffe;
  FUN_0000941c(iVar2,param_2,*(undefined1 *)(iVar1 + 8));
  *(uint *)(*(int *)(iVar1 + 4) + iVar3) = *(uint *)(*(int *)(iVar1 + 4) + iVar3) | 1;
  return 0;
}


