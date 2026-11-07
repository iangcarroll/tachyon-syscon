/* UNREVIEWED Ghidra output: FUN_0000a0d4 @ 0000a0d4 */

undefined8
FUN_0000a0d4(undefined4 param_1,uint *param_2,uint *param_3,undefined4 param_4,code *param_5)

{
  int iVar1;
  undefined4 uVar2;
  int iVar3;
  uint uVar4;
  uint uVar5;
  uint *puVar6;
  
  uVar4 = param_2[4];
  if ((int)param_2[4] < (int)param_2[2]) {
    uVar4 = param_2[2];
  }
  *param_3 = uVar4;
  if (*(char *)((int)param_2 + 0x43) != '\0') {
    *param_3 = uVar4 + 1;
  }
  if ((int)(*param_2 << 0x1a) < 0) {
    *param_3 = *param_3 + 2;
  }
  uVar4 = *param_2 & 6;
  puVar6 = param_3;
  if ((*param_2 & 6) == 0) {
    for (; (int)uVar4 < (int)(param_2[3] - *param_3); uVar4 = uVar4 + 1) {
      iVar1 = (*param_5)(param_1,param_4,(int)param_2 + 0x19,1,param_1,param_4,puVar6);
      if (iVar1 == -1) goto LAB_0000a17c;
    }
  }
  iVar1 = -(uint)(*(char *)((int)param_2 + 0x43) == '\0');
  iVar3 = iVar1 + 1;
  if ((int)(*param_2 << 0x1a) < 0) {
    *(undefined1 *)((int)param_2 + iVar1 + 0x44) = 0x30;
    iVar3 = iVar1 + 3;
    *(undefined1 *)((int)param_2 + iVar1 + 0x45) = *(undefined1 *)((int)param_2 + 0x45);
  }
  iVar1 = (*param_5)(param_1,param_4,(int)param_2 + 0x43,iVar3);
  if (iVar1 == -1) {
LAB_0000a17c:
    uVar2 = 0xffffffff;
  }
  else {
    uVar4 = 0;
    if ((*param_2 & 6) == 4) {
      uVar4 = param_2[3] - *param_3 & (int)~(param_2[3] - *param_3) >> 0x1f;
    }
    if ((int)param_2[4] < (int)param_2[2]) {
      uVar4 = uVar4 + (param_2[2] - param_2[4]);
    }
    for (uVar5 = 0; uVar4 != uVar5; uVar5 = uVar5 + 1) {
      iVar1 = (*param_5)(param_1,param_4,(int)param_2 + 0x1a,1);
      if (iVar1 == -1) goto LAB_0000a17c;
    }
    uVar2 = 0;
  }
  return CONCAT44(param_1,uVar2);
}


