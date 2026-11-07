/* UNREVIEWED Ghidra output: FUN_0000a980 @ 0000a980 */

uint * FUN_0000a980(undefined4 *param_1,uint param_2,undefined4 param_3,undefined4 param_4)

{
  int *piVar1;
  int iVar2;
  uint *puVar3;
  uint uVar4;
  uint *puVar5;
  uint *puVar6;
  uint uVar7;
  
  uVar7 = (param_2 + 3 & 0xfffffffc) + 8;
  if (uVar7 < 0xc) {
    uVar7 = 0xc;
  }
  else if ((int)uVar7 < 0) goto LAB_0000a9d4;
  if (param_2 <= uVar7) {
    FUN_0000aaac(param_1);
    piVar1 = DAT_0000aa38;
    puVar3 = (uint *)*DAT_0000aa34;
    puVar6 = (uint *)*DAT_0000aa34;
    do {
      if (puVar6 == (uint *)0x0) {
        if (*DAT_0000aa38 == 0) {
          iVar2 = FUN_0000aa88(param_1,0,puVar3,0,param_4);
          *piVar1 = iVar2;
        }
        puVar3 = (uint *)FUN_0000aa88(param_1,uVar7);
        if ((puVar3 == (uint *)0xffffffff) ||
           ((puVar6 = (uint *)((int)puVar3 + 3U & 0xfffffffc), puVar3 != puVar6 &&
            (iVar2 = FUN_0000aa88(param_1,(int)puVar6 - (int)puVar3), iVar2 == -1)))) {
          *param_1 = 0xc;
          FUN_0000aabc(param_1);
          return (uint *)0x0;
        }
LAB_0000a9ea:
        *puVar6 = uVar7;
LAB_0000a9f6:
        FUN_0000aabc(param_1);
        puVar5 = puVar6 + 1;
        puVar3 = (uint *)((int)puVar6 + 0xbU & 0xfffffff8);
        if (puVar3 == puVar5) {
          return puVar3;
        }
        *(int *)((int)puVar6 + ((int)puVar3 - (int)puVar5)) = (int)puVar5 - (int)puVar3;
        return puVar3;
      }
      uVar4 = *puVar6 - uVar7;
      if (-1 < (int)uVar4) {
        if (0xb < uVar4) {
          *puVar6 = uVar4;
          puVar6 = (uint *)((int)puVar6 + uVar4);
          goto LAB_0000a9ea;
        }
        if (puVar3 == puVar6) {
          *DAT_0000aa34 = puVar6[1];
        }
        else {
          puVar3[1] = puVar6[1];
        }
        goto LAB_0000a9f6;
      }
      puVar3 = puVar6;
      puVar6 = (uint *)puVar6[1];
    } while( true );
  }
LAB_0000a9d4:
  *param_1 = 0xc;
  return (uint *)0x0;
}


