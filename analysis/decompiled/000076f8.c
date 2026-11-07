/* UNREVIEWED Ghidra output: vector_15 @ 000076f8 */

void vector_15(void)

{
  uint *puVar1;
  uint uVar2;
  uint *puVar3;
  int iVar4;
  int iVar5;
  
  puVar1 = DAT_00007764;
  iVar5 = 0;
  uVar2 = *DAT_00007764;
  puVar3 = DAT_00007764 + 1;
  *DAT_00007764 = uVar2 + 1;
  puVar1[1] = *puVar3 + (uint)(0xfffffffe < uVar2);
  iVar4 = DAT_00007768;
  do {
    puVar3 = (uint *)(DAT_00007768 + iVar5 * 0x18);
    if (puVar3[4] != 0) {
      if ((puVar1[1] - puVar3[1] != (uint)(*puVar1 < *puVar3)) ||
         (*(uint *)(iVar4 + 8) <= *puVar1 - *puVar3)) {
        puVar3 = (uint *)(DAT_00007768 + iVar5 * 0x18);
        (*(code *)puVar3[4])(*(undefined4 *)(iVar4 + 0x14));
        if (*(char *)(iVar4 + 0xc) == '\0') {
          uVar2 = puVar1[1];
          *puVar3 = *puVar1;
          puVar3[1] = uVar2;
        }
        else {
          puVar3[4] = 0;
          *(undefined4 *)(iVar4 + 0x14) = 0;
        }
      }
    }
    iVar5 = iVar5 + 1;
    iVar4 = iVar4 + 0x18;
  } while (iVar5 != 4);
  return;
}


