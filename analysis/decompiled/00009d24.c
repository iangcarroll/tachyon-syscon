/* UNREVIEWED Ghidra output: FUN_00009d24 @ 00009d24 */

uint FUN_00009d24(undefined4 param_1,uint param_2,uint *param_3)

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  
  if (param_2 == 0xffffffff) {
LAB_00009d2c:
    uVar4 = 0xffffffff;
  }
  else {
    *(ushort *)(param_3 + 3) = (ushort)param_3[3] & 0xffdf;
    uVar3 = param_3[1];
    uVar4 = param_2 & 0xff;
    if (param_3[0xd] == 0) {
      uVar2 = *param_3;
      if (((param_3[4] != 0) && (param_3[4] < uVar2)) && (*(byte *)(uVar2 - 1) == uVar4)) {
        *param_3 = uVar2 - 1;
        goto LAB_00009d58;
      }
      param_3[0x10] = uVar3;
      param_3[0xd] = (uint)(param_3 + 0x11);
      param_3[0xe] = 3;
      param_3[0xf] = uVar2;
      *(undefined1 *)((int)param_3 + 0x46) = (char)param_2;
      *param_3 = (uint)((int)param_3 + 0x46);
      uVar3 = 1;
    }
    else {
      if (((int)param_3[0xe] <= (int)uVar3) && (iVar1 = FUN_0000a830(param_1,param_3), iVar1 != 0))
      goto LAB_00009d2c;
      uVar3 = *param_3;
      *param_3 = uVar3 - 1;
      *(char *)(uVar3 - 1) = (char)param_2;
      uVar3 = param_3[1];
LAB_00009d58:
      uVar3 = uVar3 + 1;
    }
    param_3[1] = uVar3;
  }
  return uVar4;
}


