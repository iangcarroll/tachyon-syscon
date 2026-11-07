/* UNREVIEWED Ghidra output: FUN_00003808 @ 00003808 */

longlong FUN_00003808(uint param_1,undefined4 param_2,undefined4 param_3)

{
  int iVar1;
  int iVar2;
  int iVar3;
  uint uStack_18;
  undefined4 uStack_14;
  undefined4 uStack_10;
  
  uStack_18 = param_1;
  uStack_14 = param_2;
  uStack_10 = param_3;
  FUN_0000975a(&uStack_18,0,8);
  iVar3 = 4;
  do {
    iVar1 = FUN_000082f0(0,&uStack_18);
    iVar2 = DAT_00003860;
    if (iVar1 == 0) goto LAB_0000384e;
    iVar3 = iVar3 + -1;
  } while (iVar3 != 0);
  iVar3 = FUN_000098dc(DAT_00003860,0x2f);
  if (iVar3 != 0) {
    iVar2 = FUN_000098dc(iVar2,0x2f);
    iVar2 = iVar2 + 1;
  }
  FUN_00002678(iVar2,0x5a,DAT_00003864);
LAB_0000384e:
  if (param_1 != 0) {
    FUN_000037e4();
  }
  *DAT_00003868 = 1;
  return (ulonglong)uStack_18 << 0x20;
}


