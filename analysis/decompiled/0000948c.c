/* UNREVIEWED Ghidra output: FUN_0000948c @ 0000948c */

undefined8 FUN_0000948c(int param_1,uint *param_2,undefined4 param_3)

{
  char cVar1;
  int iVar2;
  undefined4 uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  int iVar7;
  
  iVar7 = param_1;
  if (*(char *)((int)param_2 + 5) != '\0') {
    cVar1 = (char)param_2[1];
    if (cVar1 == '\0') {
      FUN_00009450(param_1,0x88,2,0,param_1,param_2,param_3);
      uVar3 = 0x88;
    }
    else if (cVar1 == ' ') {
      FUN_00009450(param_1,DAT_000095e0,2,0x20,param_1,param_2,param_3);
      uVar3 = DAT_000095e0;
    }
    else {
      FUN_00009450(param_1,0x280,2,cVar1,param_1,param_2,param_3);
      uVar3 = 0x280;
    }
    FUN_00009450(param_1,uVar3,3);
    FUN_0000942c(param_1,0,0,2);
    FUN_0000942c(param_1,0,0,3);
    *(undefined4 *)(param_1 + DAT_000095d0) = 0;
    *(undefined4 *)(param_1 + DAT_000095d4) = 0;
    FUN_00009470(param_1,0,0,2);
    FUN_00009470(param_1,0,0,3);
  }
  iVar2 = DAT_000095d8;
  uVar4 = (uint)*(byte *)((int)param_2 + 6);
  uVar6 = (uint)(byte)param_2[1];
  uVar5 = *param_2;
  if (uVar6 == 0) {
    *(uint *)(param_1 + DAT_000095dc) = uVar5 - 1;
    FUN_00009450(param_1,0x88,0);
    uVar3 = 0x88;
  }
  else {
    if (uVar6 == 0x20) {
      *(uint *)(param_1 + DAT_000095dc) = uVar5 - 1;
      FUN_00009450(param_1,DAT_000095e0,0);
      FUN_00009450(param_1,DAT_000095e0,1);
      *(uint *)(param_1 + iVar2) =
           (*(uint *)(param_1 + iVar2) ^ 0x20000000) & 0x30000000 ^ *(uint *)(param_1 + iVar2);
      goto LAB_0000957e;
    }
    *(uint *)(param_1 + DAT_000095dc) = uVar5 >> 1;
    FUN_00009450(param_1,0x280,0);
    uVar3 = 0x280;
  }
  FUN_00009450(param_1,uVar3,1);
LAB_0000957e:
  FUN_0000942c(param_1,0,0);
  FUN_0000942c(param_1,0,0,1);
  *(undefined4 *)(param_1 + DAT_000095e4) = 0;
  *(undefined4 *)(param_1 + DAT_000095e8) = 0;
  FUN_00009470(param_1,0,0,0);
  FUN_00009470(param_1,0,0,1);
  *(uint *)(param_1 + iVar2) =
       ((uVar4 | uVar6 | 2) ^ *(uint *)(param_1 + iVar2)) & DAT_000095ec ^
       *(uint *)(param_1 + iVar2);
  return CONCAT44(uVar4,iVar7);
}


