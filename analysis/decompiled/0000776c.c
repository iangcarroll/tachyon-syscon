/* UNREVIEWED Ghidra output: FUN_0000776c @ 0000776c */

void FUN_0000776c(void)

{
  char *pcVar1;
  undefined4 *puVar2;
  int iVar3;
  undefined4 uVar4;
  
  iVar3 = DAT_000077ac;
  puVar2 = DAT_000077a4;
  pcVar1 = DAT_000077a0;
  if (*DAT_000077a0 == '\0') {
    DAT_000077a4[1] = DAT_000077a8;
    *(uint *)(iVar3 + 0x20) = *(uint *)(iVar3 + 0x20) & 0xffffff | 0xc0000000;
    puVar2[2] = 0;
    uVar4 = DAT_000077b0;
    *puVar2 = 7;
    FUN_0000975a(uVar4,0,0x60);
    *pcVar1 = '\x01';
  }
  return;
}


