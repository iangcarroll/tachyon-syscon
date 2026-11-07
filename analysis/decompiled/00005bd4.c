/* UNREVIEWED Ghidra output: FUN_00005bd4 @ 00005bd4 */

undefined4 FUN_00005bd4(uint param_1,int param_2)

{
  int iVar1;
  undefined4 uVar2;
  
  iVar1 = DAT_00005bf8;
  if (100 < param_1) {
    param_1 = 100;
  }
  *(char *)(DAT_00005bf8 + 4) = (char)param_1;
  uVar2 = FUN_00001438(param_1 & 0xff);
  *(undefined4 *)(iVar1 + 8) = uVar2;
  if (param_2 != 0) {
    FUN_00005b48();
  }
  return 0;
}


