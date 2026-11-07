/* UNREVIEWED Ghidra output: FUN_00003b0c @ 00003b0c */

int FUN_00003b0c(int param_1)

{
  int iVar1;
  
  if (*(char *)(param_1 + 0x10) == '\0') {
    if (*(uint *)(param_1 + 8) < *(uint *)(param_1 + 0xc)) {
      iVar1 = (*(int *)(param_1 + 8) + *(int *)(param_1 + 4)) - *(int *)(param_1 + 0xc);
    }
    else {
      iVar1 = *(int *)(param_1 + 8) - *(int *)(param_1 + 0xc);
    }
  }
  else {
    iVar1 = *(int *)(param_1 + 4);
  }
  return iVar1;
}


