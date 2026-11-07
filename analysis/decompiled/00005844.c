/* UNREVIEWED Ghidra output: FUN_00005844 @ 00005844 */

void FUN_00005844(void)

{
  char *pcVar1;
  char *pcVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  bool bVar6;
  
  iVar4 = FUN_000080f8(*DAT_000058dc);
  pcVar2 = DAT_000058e4;
  pcVar1 = DAT_000058e0;
  if (*DAT_000058e0 == '\0') {
    if (iVar4 == 0) {
      FUN_00006a28();
      goto LAB_00005862;
    }
    FUN_00006a48();
LAB_000058b8:
    bVar6 = true;
    if (*pcVar2 == -1) goto LAB_000058c0;
  }
  else {
    if (iVar4 != 0) goto LAB_000058b8;
LAB_00005862:
    bVar6 = *pcVar1 == '\0';
    if (*pcVar2 == -1) {
      *DAT_000058e8 = 0;
      *DAT_000058ec = 0;
      *DAT_000058f0 = 0;
      *DAT_000058f4 = 0;
      iVar4 = FUN_00006690();
      if (iVar4 == 0) {
        iVar4 = FUN_00003178();
      }
      else {
        iVar4 = FUN_0000315c();
      }
      iVar3 = DAT_000058fc;
      iVar4 = iVar4 * 1000;
      iVar5 = iVar4 + DAT_000058f8;
      *(int *)(DAT_000058fc + 4) = iVar4;
      *(int *)(iVar3 + 0xc) = iVar4;
      *(int *)(iVar3 + 0x10) = iVar5;
      *(int *)(iVar3 + 0x18) = iVar5;
    }
  }
  FUN_0000781c(10,0,DAT_00005900);
  if (!bVar6) {
    return;
  }
LAB_000058c0:
  FUN_00008148(0,0,DAT_00005904);
  return;
}


