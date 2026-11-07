/* UNREVIEWED Ghidra output: FUN_000062ec @ 000062ec */

uint FUN_000062ec(uint param_1,int param_2)

{
  int iVar1;
  undefined4 uVar2;
  undefined4 extraout_r1;
  uint uVar3;
  undefined4 uVar4;
  uint uVar5;
  
  iVar1 = FUN_00007d54();
  if (param_1 < 7) {
    uVar3 = *(uint *)(param_1 * 4 + DAT_00006364);
  }
  else {
    uVar3 = DAT_00006380;
  }
  uVar5 = uVar3;
  if (499 < iVar1) {
    if (uVar3 < DAT_00006368) {
      uVar5 = DAT_00006368;
    }
    if (uVar3 <= DAT_0000636c) {
      uVar2 = FUN_000001fc(iVar1,10);
      uVar4 = *(undefined4 *)(param_1 * 4 + DAT_00006370);
      FUN_000003c8(iVar1,10);
      FUN_00008f88(3,DAT_00006378,DAT_00006374,uVar2,extraout_r1,uVar4);
    }
  }
  iVar1 = 0;
  while( true ) {
    if (param_2 == iVar1) {
      return uVar5;
    }
    if (DAT_0000637c < uVar5) break;
    uVar5 = uVar5 << 1;
    iVar1 = iVar1 + 1;
  }
  return DAT_00006380;
}


