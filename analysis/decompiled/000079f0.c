/* UNREVIEWED Ghidra output: Reset_Handler @ 000079f0 */

void Reset_Handler(void)

{
  undefined4 *puVar1;
  undefined4 uVar2;
  undefined4 *puVar3;
  undefined4 *puVar4;
  undefined4 *puVar5;
  
  puVar4 = DAT_00007a38;
  puVar3 = DAT_00007a30;
  for (puVar5 = DAT_00007a34; puVar1 = DAT_00007a44, puVar5 < puVar4; puVar5 = puVar5 + 1) {
    uVar2 = *puVar3;
    puVar3 = puVar3 + 1;
    *puVar5 = uVar2;
  }
  puVar4 = DAT_00007a3c;
  for (puVar3 = DAT_00007a40; puVar5 = DAT_00007a4c, puVar3 < puVar1; puVar3 = puVar3 + 1) {
    uVar2 = *puVar4;
    puVar4 = puVar4 + 1;
    *puVar3 = uVar2;
  }
  for (puVar4 = DAT_00007a48; puVar4 < puVar5; puVar4 = puVar4 + 1) {
    *puVar4 = 0;
  }
  FUN_000096d4();
  FUN_00003b34();
  vector_3();
  return;
}


