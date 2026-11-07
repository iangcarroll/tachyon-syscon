/* UNREVIEWED Ghidra output: FUN_00009a60 @ 00009a60 */

undefined4 FUN_00009a60(undefined4 *param_1,int *param_2,undefined4 param_3,uint param_4)

{
  int iVar1;
  int iVar2;
  uint uVar3;
  uint uVar4;
  
  if ((uint)param_2[2] <= param_4) {
    uVar4 = param_2[2];
    if ((*(ushort *)(param_2 + 3) & 0x480) != 0) {
      iVar2 = *param_2 - param_2[4];
      uVar3 = param_4 + 1 + iVar2;
      uVar4 = (param_2[5] * 3) / 2;
      if (uVar4 < uVar3) {
        uVar4 = uVar3;
      }
      if ((int)((uint)*(ushort *)(param_2 + 3) << 0x15) < 0) {
        iVar1 = FUN_0000a980(param_1,uVar4);
        if (iVar1 == 0) {
LAB_00009aae:
          *param_1 = 0xc;
          *(ushort *)(param_2 + 3) = *(ushort *)(param_2 + 3) | 0x40;
          return 0xffffffff;
        }
        FUN_00009748(iVar1,param_2[4],iVar2);
        *(ushort *)(param_2 + 3) = (ushort)DAT_00009b20 & *(ushort *)(param_2 + 3) | 0x80;
      }
      else {
        iVar1 = FUN_0000aa3c(param_1,param_2[4],uVar4);
        if (iVar1 == 0) {
          FUN_0000a8ec(param_1,param_2[4]);
          goto LAB_00009aae;
        }
      }
      param_2[4] = iVar1;
      *param_2 = iVar1 + iVar2;
      param_2[5] = uVar4;
      param_2[2] = uVar4 - iVar2;
      uVar4 = param_4;
    }
    if (uVar4 <= param_4) goto LAB_00009aee;
  }
  uVar4 = param_4;
LAB_00009aee:
  FUN_0000a8c6(*param_2,param_3,uVar4);
  param_2[2] = param_2[2] - uVar4;
  *param_2 = *param_2 + uVar4;
  return 0;
}


