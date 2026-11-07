/* UNREVIEWED Ghidra output: FUN_0000a69c @ 0000a69c */

byte * FUN_0000a69c(int param_1,byte *param_2)

{
  uint uVar1;
  int iVar2;
  byte *pbVar3;
  uint uVar4;
  uint uVar5;
  bool bVar6;
  
  uVar4 = (uint)*param_2;
  bVar6 = uVar4 == 0x5e;
  if (bVar6) {
    uVar4 = (uint)param_2[1];
    param_2 = param_2 + 2;
  }
  else {
    param_2 = param_2 + 1;
  }
  iVar2 = param_1;
  do {
    *(bool *)iVar2 = bVar6;
    iVar2 = iVar2 + 1;
  } while (iVar2 != param_1 + 0x100);
  if (uVar4 == 0) {
    return param_2 + -1;
  }
LAB_0000a6ce:
  do {
    *(bool *)(param_1 + uVar4) = !bVar6;
    pbVar3 = param_2;
    while( true ) {
      uVar5 = (uint)*pbVar3;
      param_2 = pbVar3 + 1;
      if (uVar5 != 0x2d) break;
      uVar5 = (uint)pbVar3[1];
      if ((uVar5 == 0x5d) || ((int)uVar5 < (int)uVar4)) {
        uVar4 = 0x2d;
        goto LAB_0000a6ce;
      }
      pbVar3 = pbVar3 + 2;
      uVar1 = uVar4;
      do {
        uVar1 = uVar1 + 1;
        *(bool *)(param_1 + uVar1) = !bVar6;
      } while ((int)uVar1 < (int)uVar5);
      iVar2 = 0;
      if ((int)uVar4 < (int)uVar5) {
        iVar2 = (uVar5 - uVar4) + -1;
      }
      uVar4 = uVar4 + 1 + iVar2;
    }
    if (uVar5 == 0x5d) {
      return param_2;
    }
    if (uVar5 == 0) {
      return pbVar3;
    }
    uVar4 = uVar5;
  } while( true );
}


