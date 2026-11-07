/* UNREVIEWED Ghidra output: FUN_0000781c @ 0000781c */

undefined4 FUN_0000781c(undefined4 param_1,undefined1 param_2,int param_3,undefined4 param_4)

{
  undefined4 *puVar1;
  undefined4 uVar2;
  undefined4 *puVar3;
  uint uVar4;
  
  uVar4 = 0;
  do {
    if (*(int *)(DAT_00007878 + uVar4 * 0x18 + 0x10) == param_3) goto LAB_0000785a;
    uVar4 = uVar4 + 1;
  } while (uVar4 != 4);
  uVar4 = 0;
  while (*(int *)(DAT_00007878 + uVar4 * 0x18 + 0x10) != 0) {
    uVar4 = uVar4 + 1;
    if (uVar4 == 4) {
      return 0xffffffff;
    }
  }
LAB_0000785a:
  puVar3 = (undefined4 *)(DAT_00007878 + (uVar4 & 0xff) * 0x18);
  puVar3[5] = param_4;
  puVar1 = DAT_0000787c;
  puVar3[4] = param_3;
  puVar3[2] = param_1;
  uVar2 = puVar1[1];
  *puVar3 = *puVar1;
  puVar3[1] = uVar2;
  *(undefined1 *)(puVar3 + 3) = param_2;
  return 0;
}


