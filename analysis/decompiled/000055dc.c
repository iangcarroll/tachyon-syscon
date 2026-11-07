/* UNREVIEWED Ghidra output: FUN_000055dc @ 000055dc */

void FUN_000055dc(int param_1)

{
  undefined8 *puVar1;
  undefined8 uVar2;
  
  FUN_00008f88(3,DAT_0000561c,DAT_00005618,*(undefined4 *)(param_1 * 4 + DAT_00005614));
  puVar1 = DAT_00005624;
  *DAT_00005620 = (char)param_1;
  *DAT_00005628 = 0;
  if (param_1 == 0) {
    *(undefined4 *)puVar1 = 0;
    *(undefined4 *)((int)puVar1 + 4) = 0;
  }
  else {
    uVar2 = FUN_000077b4();
    *puVar1 = uVar2;
  }
  return;
}


