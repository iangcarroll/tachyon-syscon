/* UNREVIEWED Ghidra output: FUN_00005638 @ 00005638 */

/* WARNING: Removing unreachable block (ram,0x0000565c) */

longlong FUN_00005638(void)

{
  ulonglong *puVar1;
  ulonglong uVar2;
  
  puVar1 = DAT_0000566c;
  if ((int)*DAT_0000566c != 0 || *(int *)((int)DAT_0000566c + 4) != 0) {
    uVar2 = FUN_000077b4();
    if (*puVar1 < uVar2) {
      return uVar2 - *puVar1;
    }
  }
  return 0;
}


