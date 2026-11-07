/* UNREVIEWED Ghidra output: FUN_00005dc8 @ 00005dc8 */

bool FUN_00005dc8(undefined1 *param_1)

{
  undefined *puVar1;
  
  if (param_1 != (undefined1 *)0x0) {
    *param_1 = *PTR_DAT_00005dec;
    puVar1 = PTR_DAT_00005df0;
    param_1[1] = PTR_DAT_00005df0[1];
    param_1[2] = puVar1[2];
    param_1[3] = puVar1[3];
    param_1[4] = puVar1[4];
    param_1[5] = *puVar1;
  }
  return param_1 != (undefined1 *)0x0;
}


