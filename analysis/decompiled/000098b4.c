/* UNREVIEWED Ghidra output: FUN_000098b4 @ 000098b4 */

void FUN_000098b4(char *param_1,char *param_2,int param_3)

{
  char cVar1;
  char *pcVar2;
  char *pcVar3;
  
  do {
    pcVar3 = param_1;
    if (param_3 == 0) break;
    cVar1 = *param_2;
    param_3 = param_3 + -1;
    pcVar3 = param_1 + 1;
    *param_1 = cVar1;
    param_2 = param_2 + 1;
    param_1 = pcVar3;
  } while (cVar1 != '\0');
  pcVar2 = pcVar3 + param_3;
  for (; pcVar3 != pcVar2; pcVar3 = pcVar3 + 1) {
    *pcVar3 = '\0';
  }
  return;
}


