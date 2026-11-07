/* UNREVIEWED Ghidra output: FUN_00005c38 @ 00005c38 */

undefined4 FUN_00005c38(undefined1 *param_1)

{
  undefined1 uVar1;
  undefined1 uVar2;
  int iVar3;
  undefined4 uVar4;
  
  iVar3 = DAT_00005c64;
  if (param_1 == (undefined1 *)0x0) {
    uVar4 = 0xffffffff;
  }
  else {
    uVar1 = param_1[2];
    uVar2 = *param_1;
    *(undefined1 *)(DAT_00005c64 + 2) = param_1[1];
    *(undefined1 *)(iVar3 + 1) = uVar2;
    *(undefined1 *)(iVar3 + 3) = uVar1;
    FUN_00005bd4(param_1[3],0);
    uVar4 = FUN_00005bfc(param_1[4],1);
  }
  return uVar4;
}


