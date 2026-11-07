/* UNREVIEWED Ghidra output: FUN_00009828 @ 00009828 */

char * FUN_00009828(char *param_1,char param_2)

{
  while( true ) {
    if (*param_1 == '\0') {
      return (char *)((uint)param_1 & -(uint)(param_2 == '\0'));
    }
    if (*param_1 == param_2) break;
    param_1 = param_1 + 1;
  }
  return param_1;
}


