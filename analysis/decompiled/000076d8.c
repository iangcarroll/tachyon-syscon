/* UNREVIEWED Ghidra output: FUN_000076d8 @ 000076d8 */

char FUN_000076d8(void)

{
  char cVar1;
  
  cVar1 = *(char *)(DAT_000076ec + 0x68);
  if (cVar1 == '\0') {
    cVar1 = *(char *)(DAT_000076ec + 0xd4);
  }
  return cVar1;
}


