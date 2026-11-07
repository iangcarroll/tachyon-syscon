/* UNREVIEWED Ghidra output: FUN_00002678 @ 00002678 */

void FUN_00002678(undefined4 param_1,undefined4 param_2,undefined4 param_3)

{
  int iVar1;
  short sVar2;
  undefined1 auStack_1c [4];
  undefined1 local_18;
  undefined4 local_14;
  
  FUN_00008f88(1,DAT_00002720,DAT_0000271c,param_3,param_1,param_2,1);
  disableIRQinterrupts();
  *DAT_00002724 = *DAT_00002724 & 0xfffffffd;
  FUN_0000975a(auStack_1c,0,8);
  local_18 = 1;
  local_14 = 2;
  FUN_00007f58(2,auStack_1c);
  FUN_00007f58(1,auStack_1c);
  FUN_00007f58(3,auStack_1c);
  sVar2 = 0x14;
  do {
    FUN_000080ac(3);
    FUN_00007ae8(DAT_00002728);
    FUN_000079d0();
    iVar1 = FUN_000080f8(0);
    if (iVar1 == 0) {
      FUN_00007ae8(DAT_0000272c);
      iVar1 = FUN_000080f8(0);
      if (iVar1 == 0) {
        DataSynchronizationBarrier(0xf);
        *(undefined4 *)(DAT_00002730 + 0xc) = DAT_00002734;
        DataSynchronizationBarrier(0xf);
        do {
                    /* WARNING: Do nothing block with infinite loop */
        } while( true );
      }
    }
    sVar2 = sVar2 + -1;
  } while (sVar2 != 0);
  DataSynchronizationBarrier(0xf);
  *(undefined4 *)(DAT_00002730 + 0xc) = DAT_00002734;
  DataSynchronizationBarrier(0xf);
  do {
                    /* WARNING: Do nothing block with infinite loop */
  } while( true );
}


