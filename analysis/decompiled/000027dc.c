/* UNREVIEWED Ghidra output: FUN_000027dc @ 000027dc */

undefined4 FUN_000027dc(byte *param_1)

{
  int iVar1;
  uint uVar2;
  byte *pbVar3;
  
  pbVar3 = param_1 + 0x1f;
  while( true ) {
    uVar2 = (uint)*param_1;
    if ((uVar2 == 0) || (uVar2 == 0x3b)) {
      return 1;
    }
    iVar1 = FUN_0000971c(uVar2);
    if (((iVar1 == 0) && (uVar2 != 0x5f)) && (1 < uVar2 - 0x2d)) break;
    param_1 = param_1 + 1;
    if (pbVar3 == param_1) {
      return 0;
    }
  }
  return 0;
}


