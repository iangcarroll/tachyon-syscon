/* UNREVIEWED Ghidra output: FUN_0000a830 @ 0000a830 */

undefined8 FUN_0000a830(undefined4 param_1,int *param_2)

{
  int iVar1;
  undefined4 uVar2;
  int *piVar3;
  int iVar4;
  
  piVar3 = (int *)param_2[0xd];
  if (piVar3 == param_2 + 0x11) {
    iVar1 = FUN_0000a980(param_1,0x400);
    if (iVar1 != 0) {
      param_2[0xd] = iVar1;
      param_2[0xe] = 0x400;
      *(undefined1 *)(iVar1 + DAT_0000a8a0) = *(undefined1 *)((int)param_2 + 0x46);
      *(undefined1 *)(iVar1 + DAT_0000a8a4) = *(undefined1 *)((int)param_2 + 0x45);
      iVar4 = DAT_0000a8a8;
      *(char *)(iVar1 + DAT_0000a8a8) = (char)*piVar3;
      *param_2 = iVar1 + iVar4;
LAB_0000a874:
      uVar2 = 0;
      goto LAB_0000a850;
    }
  }
  else {
    iVar4 = param_2[0xe];
    iVar1 = FUN_0000aa3c(param_1,piVar3,iVar4 << 1);
    if (iVar1 != 0) {
      FUN_00009748(iVar1 + iVar4,iVar1,iVar4);
      *param_2 = iVar1 + iVar4;
      param_2[0xd] = iVar1;
      param_2[0xe] = iVar4 << 1;
      goto LAB_0000a874;
    }
  }
  uVar2 = 0xffffffff;
LAB_0000a850:
  return CONCAT44(param_1,uVar2);
}


