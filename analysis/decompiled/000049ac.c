/* UNREVIEWED Ghidra output: cmd_LOG @ 000049ac */

undefined4 cmd_LOG(char *param_1,code *param_2)

{
  undefined4 uVar1;
  
  uVar1 = 0;
  if (*param_1 != '0') {
    if (*param_1 != '1') {
      (*param_2)(DAT_000049cc);
      return 0;
    }
    uVar1 = 1;
  }
  FUN_00008fc0(uVar1);
  return 1;
}


