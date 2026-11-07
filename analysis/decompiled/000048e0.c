/* UNREVIEWED Ghidra output: cmd_DIAG @ 000048e0 */

undefined4 cmd_DIAG(char *param_1,code *param_2)

{
  undefined4 uVar1;
  
  uVar1 = 0;
  if (*param_1 != '0') {
    if (*param_1 != '1') {
      (*param_2)(DAT_00004900);
      return 0;
    }
    uVar1 = 1;
  }
  FUN_0000347c(uVar1);
  return 1;
}


