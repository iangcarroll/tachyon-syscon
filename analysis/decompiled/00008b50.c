/* UNREVIEWED Ghidra output: FUN_00008b50 @ 00008b50 */

undefined4 FUN_00008b50(void)

{
  undefined1 uVar1;
  undefined1 *puVar2;
  int iVar3;
  int iVar4;
  int iVar5;
  
  puVar2 = (undefined1 *)FUN_00007ac0();
  iVar4 = DAT_00008c0c;
  if (puVar2 == (undefined1 *)0x0) {
    iVar3 = FUN_000098dc(DAT_00008c0c,0x2f);
    if (iVar3 != 0) {
      iVar4 = FUN_000098dc(iVar4,0x2f);
      iVar4 = iVar4 + 1;
    }
    FUN_00002678(iVar4,0x96,DAT_00008c10);
  }
  if (-1 < (char)puVar2[0xc]) {
    *(int *)(DAT_00008c14 + 0x7c) = 1 << ((int)(char)puVar2[0xc] & 0x1fU);
    DataSynchronizationBarrier(0xf);
    InstructionSynchronizationBarrier(0xf);
  }
  iVar4 = *(int *)(puVar2 + 8);
  *(uint *)(iVar4 + DAT_00008c18) = *(uint *)(iVar4 + DAT_00008c18) & DAT_00008c1c;
  if (-1 < (char)puVar2[0xc]) {
    *(int *)(DAT_00008c20 + 0x180) = 1 << ((int)(char)puVar2[0xc] & 0x1fU);
  }
  *(uint *)(iVar4 + 0x1100) = *(uint *)(iVar4 + 0x1100) & 0xfffffffe;
  iVar3 = DAT_00008c24;
  uVar1 = *puVar2;
  *(undefined4 *)(iVar4 + DAT_00008c24) = DAT_00008c28;
  *(undefined4 *)(iVar4 + iVar3 + -4) = 0x26000000;
  iVar3 = FUN_00007a54(uVar1);
  iVar5 = FUN_00007a54(puVar2[3]);
  iVar4 = DAT_00008c2c;
  *(uint *)((uint)*(byte *)(iVar3 + 5) * 4 + DAT_00008c2c + 4) = (byte)puVar2[2] | 0x80;
  *(uint *)((uint)*(byte *)(iVar5 + 5) * 4 + iVar4 + 4) = DAT_00008c30 | (byte)puVar2[5];
  return 0;
}


