/* UNREVIEWED Ghidra output: FUN_00008c8c @ 00008c8c */

longlong FUN_00008c8c(uint param_1,undefined1 *param_2,int param_3)

{
  int iVar1;
  int iVar2;
  int iVar3;
  undefined1 *puVar4;
  
  iVar1 = FUN_00007ac0();
  iVar3 = DAT_00008ce4;
  if (iVar1 == 0) {
    iVar2 = FUN_000098dc(DAT_00008ce4,0x2f);
    if (iVar2 != 0) {
      iVar3 = FUN_000098dc(iVar3,0x2f);
      iVar3 = iVar3 + 1;
    }
    FUN_00002678(iVar3,0xb9,DAT_00008ce8);
  }
  if (*(char *)(DAT_00008cec + param_1 * 9 + 8) == '\0') {
    puVar4 = param_2 + param_3;
    for (; param_2 != puVar4; param_2 = param_2 + 1) {
      FUN_0000964c(*(undefined4 *)(iVar1 + 8),*param_2);
    }
  }
  return (ulonglong)param_1 << 0x20;
}


