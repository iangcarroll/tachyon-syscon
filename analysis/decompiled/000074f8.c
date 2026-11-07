/* UNREVIEWED Ghidra output: FUN_000074f8 @ 000074f8 */

void FUN_000074f8(void)

{
  undefined *puVar1;
  uint *puVar2;
  
  puVar1 = PTR_s_SLEP_00007530;
  FUN_00008f88(3,PTR_s_SLEP_00007530,PTR_s_Going_to_sleep_00007534);
  puVar2 = DAT_00007538;
  disableIRQinterrupts();
  *DAT_00007538 = *DAT_00007538 & 0xfffffffd;
  DataSynchronizationBarrier(0xf);
  InstructionSynchronizationBarrier(0xf);
  WaitForInterrupt();
  enableIRQinterrupts();
  *puVar2 = *puVar2 | 2;
  FUN_00008f88(3,puVar1,DAT_0000753c);
  return;
}


