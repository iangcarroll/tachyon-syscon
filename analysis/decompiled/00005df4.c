/* UNREVIEWED Ghidra output: FUN_00005df4 @ 00005df4 */

undefined * FUN_00005df4(uint param_1)

{
  undefined *puVar1;
  
  puVar1 = PTR_s_unknown_00005e04;
  if (param_1 < 10) {
    puVar1 = *(undefined **)(PTR_PTR_00005e08 + param_1 * 4);
  }
  return puVar1;
}


