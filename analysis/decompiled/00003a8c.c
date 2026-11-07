/* UNREVIEWED Ghidra output: FUN_00003a8c @ 00003a8c */

void FUN_00003a8c(undefined1 param_1)

{
  int *piVar1;
  int iVar2;
  int extraout_r1;
  
  piVar1 = DAT_00003ac8;
  if ((char)DAT_00003ac8[4] == '\0') {
    iVar2 = DAT_00003ac8[1];
    *(undefined1 *)(*DAT_00003ac8 + DAT_00003ac8[2]) = param_1;
    FUN_000001f4(piVar1[2] + 1,iVar2);
    piVar1[2] = extraout_r1;
    if (piVar1[2] == piVar1[3]) {
      *(undefined1 *)(piVar1 + 4) = 1;
    }
  }
  else {
    FUN_00008f88(1,DAT_00003ad0,DAT_00003acc,0xffffffff);
  }
  return;
}


