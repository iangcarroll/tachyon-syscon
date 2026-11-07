/* UNREVIEWED Ghidra output: FUN_0000296c @ 0000296c */

bool FUN_0000296c(int param_1,int param_2)

{
  int iVar1;
  undefined1 *puVar2;
  
  FUN_00002840();
  iVar1 = FUN_000098b4(param_2,param_1 + 0x20,0x20);
  *(undefined1 *)(param_2 + 0x1e) = 0;
  puVar2 = (undefined1 *)FUN_00009828(param_2,0x3b);
  if (puVar2 != (undefined1 *)0x0) {
    *puVar2 = 0;
  }
  return iVar1 != 0;
}


