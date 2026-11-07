/* UNREVIEWED Ghidra output: vector_17 @ 00008258 */

void vector_17(void)

{
  int iVar1;
  int *piVar2;
  code *pcVar3;
  uint uVar4;
  int iVar5;
  
  iVar1 = DAT_000082ac;
  if (*(int *)(DAT_000082a4 + DAT_000082a8) == 1) {
    uVar4 = 0;
    iVar5 = *(int *)(DAT_000082ac + 0x1020);
    do {
      piVar2 = (int *)FUN_00007a54(uVar4);
      if ((*piVar2 == iVar1) && ((uint)*(byte *)(piVar2 + 1) == (iVar5 - 1U & 0xff))) {
        pcVar3 = *(code **)(uVar4 * 8 + DAT_000082b0);
        if (pcVar3 == (code *)0x0) {
          return;
        }
        (*pcVar3)(uVar4,*(undefined4 *)(DAT_000082b0 + uVar4 * 8 + 4));
        return;
      }
      uVar4 = uVar4 + 1 & 0xff;
    } while (uVar4 != 0x19);
  }
  return;
}


