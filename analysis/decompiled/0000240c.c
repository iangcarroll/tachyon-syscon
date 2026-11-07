/* UNREVIEWED Ghidra output: FUN_0000240c @ 0000240c */

int FUN_0000240c(undefined4 param_1,int param_2)

{
  int iVar1;
  
  if (param_2 == 0) {
    iVar1 = FUN_000023d0();
    iVar1 = iVar1 + 0x20;
  }
  else {
    iVar1 = FUN_000023d0(param_2);
  }
  return iVar1;
}


