/* UNREVIEWED Ghidra output: FUN_00005afc @ 00005afc */

void FUN_00005afc(void)

{
  if (*(char *)(DAT_00005b10 + 2) != -1) {
    *(char *)(DAT_00005b10 + 2) = *(char *)(DAT_00005b10 + 2) + '\x01';
  }
  FUN_000059a0();
  return;
}


