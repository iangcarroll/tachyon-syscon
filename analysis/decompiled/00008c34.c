/* UNREVIEWED Ghidra output: FUN_00008c34 @ 00008c34 */

undefined4 FUN_00008c34(int param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  int iVar1;
  int iVar2;
  int iVar3;
  undefined4 extraout_r3;
  undefined4 uVar4;
  
  iVar1 = FUN_00007ac0();
  iVar3 = DAT_00008c80;
  if (iVar1 == 0) {
    iVar2 = FUN_000098dc(DAT_00008c80,0x2f);
    uVar4 = 0;
    if (iVar2 != 0) {
      iVar3 = FUN_000098dc(iVar3,0x2f);
      iVar3 = iVar3 + 1;
      uVar4 = extraout_r3;
    }
    FUN_00002678(iVar3,0xae,DAT_00008c84,uVar4,param_4);
  }
  if (*(char *)(DAT_00008c88 + param_1 * 9 + 8) == '\0') {
    FUN_0000964c(*(undefined4 *)(iVar1 + 8),param_2);
  }
  return 0;
}


