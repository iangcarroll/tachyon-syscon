/* UNREVIEWED Ghidra output: FUN_0000a3d8 @ 0000a3d8 */

undefined8 FUN_0000a3d8(undefined4 param_1,uint *param_2,int *param_3,undefined4 *param_4)

{
  undefined4 uVar1;
  uint uVar2;
  undefined4 *puVar3;
  int iVar4;
  int iVar5;
  byte *unaff_r7;
  
  if (param_2[2] == 0) {
    uVar2 = 1;
    if (param_2[6] != 0) {
      uVar2 = 0xffffffff;
    }
    param_2[2] = uVar2;
  }
  if (-1 < (int)(*param_2 << 0x1b)) {
    puVar3 = (undefined4 *)*param_4;
    *param_4 = puVar3 + 1;
    unaff_r7 = (byte *)*puVar3;
  }
  iVar5 = 0;
  do {
    uVar2 = param_2[6];
    if (uVar2 != 0) {
      if (uVar2 == 1) {
        if (*(char *)(param_2[5] + (uint)*(byte *)*param_3) == '\0') {
          uVar1 = 1;
          if (iVar5 == 0) goto LAB_0000a48e;
LAB_0000a46c:
          if (((*param_2 & 0x10) == 0) && (param_2[3] = param_2[3] + 1, param_2[6] != 0)) {
            *unaff_r7 = (byte)*param_2 & 0x10;
          }
          uVar1 = 0;
          param_2[4] = param_2[4] + iVar5;
LAB_0000a48e:
          return CONCAT44(param_1,uVar1);
        }
      }
      else if ((uVar2 != 2) || ((*(byte *)(DAT_0000a490 + (uint)*(byte *)*param_3) & 8) != 0))
      goto LAB_0000a46c;
    }
    iVar5 = iVar5 + 1;
    if ((*param_2 & 0x10) == 0) {
      *unaff_r7 = *(byte *)*param_3;
      unaff_r7 = unaff_r7 + 1;
    }
    iVar4 = param_3[1];
    *param_3 = *param_3 + 1;
    uVar2 = param_2[2];
    param_3[1] = iVar4 + -1;
    param_2[2] = uVar2 - 1;
    if ((uVar2 - 1 == 0) ||
       ((iVar4 + -1 < 1 && (iVar4 = (*(code *)param_2[0x60])(param_1,param_3), iVar4 != 0))))
    goto LAB_0000a46c;
  } while( true );
}


