/* UNREVIEWED Ghidra output: FUN_00007c3c @ 00007c3c */

undefined4 FUN_00007c3c(uint param_1)

{
  undefined4 uVar1;
  
  uVar1 = DAT_00007c4c;
  if (param_1 < 7) {
    uVar1 = *(undefined4 *)(param_1 * 4 + DAT_00007c50);
  }
  return uVar1;
}


