/* UNREVIEWED Ghidra output: FUN_00005e0c @ 00005e0c */

undefined * FUN_00005e0c(uint param_1)

{
  undefined *puVar1;
  
  puVar1 = PTR_s_unknown_00005e1c;
  if (param_1 < 6) {
    puVar1 = *(undefined **)(PTR_PTR_00005e20 + param_1 * 4);
  }
  return puVar1;
}


