/* UNREVIEWED Ghidra output: FUN_00008cf0 @ 00008cf0 */

int FUN_00008cf0(int param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4)

{
  char cVar1;
  int iVar2;
  int iVar3;
  undefined4 extraout_r3;
  undefined4 uVar4;
  uint uVar5;
  uint uVar6;
  
  iVar2 = FUN_00007ac0();
  iVar3 = DAT_00008d60;
  if (iVar2 == 0) {
    iVar2 = FUN_000098dc(DAT_00008d60,0x2f);
    uVar4 = 0;
    if (iVar2 != 0) {
      iVar3 = FUN_000098dc(iVar3,0x2f);
      iVar3 = iVar3 + 1;
      uVar4 = extraout_r3;
    }
    FUN_00002678(iVar3,0xc6,DAT_00008d64,uVar4,param_4);
  }
  iVar3 = 0;
  if (*(char *)(DAT_00008d68 + param_1 * 9 + 8) == '\0') {
    FUN_0000891c(param_1);
    iVar3 = DAT_00008d6c + param_1 * 0x4c;
    uVar5 = *(uint *)(iVar3 + 0x40);
    uVar6 = *(uint *)(iVar3 + 0x44);
    cVar1 = *(char *)(iVar3 + 0x48);
    FUN_00008938(param_1);
    iVar3 = 0x40;
    if (cVar1 == '\0') {
      if (uVar5 < uVar6) {
        uVar5 = uVar5 + 0x40;
      }
      iVar3 = uVar5 - uVar6;
    }
  }
  return iVar3;
}


