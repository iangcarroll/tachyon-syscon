/* UNREVIEWED Ghidra output: FUN_0000517c @ 0000517c */

char FUN_0000517c(void)

{
  uint *puVar1;
  char cVar2;
  uint uVar3;
  undefined8 uVar4;
  
  puVar1 = DAT_000051bc;
  cVar2 = *DAT_000051b8;
  if ((cVar2 == '\0') && (*DAT_000051bc != 0 || DAT_000051bc[1] != 0)) {
    uVar4 = FUN_000077b4(0);
    uVar3 = *puVar1;
    cVar2 = '\x01';
    if (((int)((ulonglong)uVar4 >> 0x20) - puVar1[1] != (uint)((uint)uVar4 < uVar3)) ||
       (1999 < (uint)uVar4 - uVar3)) {
      cVar2 = '\0';
    }
  }
  return cVar2;
}


